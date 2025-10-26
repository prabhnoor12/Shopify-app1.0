"""
Service for product CRUD and Shopify sync logic.
"""

import logging
from typing import List, Optional
import re
from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
import asyncio
from openai import OpenAI, APIError

from ..dependencies.config import settings
from ..crud import product_crud
from ..models.product import Product
from ..schemas.product import ProductCreate, ProductUpdate, Product as ProductSchema
from ..schemas.enums import ProductStatus
from ..services.audit_service import AuditLogService
from ..services.content_version_service import ContentVersionService
from ..services.order_service import OrderService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for production readiness
HTTP_CLIENT_TIMEOUT = 15.0  # seconds
PLACEHOLDER_PATTERNS = [
    "lorem ipsum",
    "insert description here",
    "coming soon",
    "tbd",
    r"\[\s*insert.*description\s*\]",  # Catches [insert description]
]


class ProductService:
    """
    Service layer for handling product-related business logic and Shopify integration.
    """

    def __init__(
        self,
        db: Session,
        audit_log_service: AuditLogService,
        content_version_service: ContentVersionService,
    ):
        """
        Initializes the ProductService with a database session and other services.

        Args:
            db (Session): The SQLAlchemy database session.
            audit_log_service (AuditLogService): The service for logging audit trails.
            content_version_service (ContentVersionService): The service for managing content versions.
        """
        self.db = db
        self.audit_log_service = audit_log_service
        self.content_version_service = content_version_service
        self.order_service = OrderService()  # Initialize OrderService
        self.shopify_api_version = settings.SHOPIFY_API_VERSION
        self.shopify_base_url = f"https://{settings.SHOPIFY_STORE_DOMAIN}/admin/api/{self.shopify_api_version}"
        self.shopify_headers = {
            "X-Shopify-Access-Token": settings.SHOPIFY_ADMIN_API_KEY,
            "Content-Type": "application/json",
        }

        # Production-ready clients
        self._http_client = httpx.AsyncClient(timeout=HTTP_CLIENT_TIMEOUT)
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
        await self.order_service.close()

    async def analyze_product_performance(self, shop_id: int, time_period_days: int = 30):
        """
        Analyzes product sales performance and provides AI-driven insights.
        """
        logger.info(f"Starting product performance analysis for shop {shop_id}.")
        try:
            # 1. Get sales data
            sales_data = await self.order_service.get_sales_data_for_products(time_period_days)
            if not sales_data:
                logger.info("No sales data found for the given period.")
                return

            # 2. Get all products for the shop
            products = self.db.query(Product).filter(Product.shop_id == shop_id).all()
            if not products:
                logger.info(f"No products found for shop {shop_id}.")
                return

            # 3. Prepare data for AI analysis
            performance_data_str = ""
            for product in products:
                data = sales_data.get(product.shopify_product_id, {"units_sold": 0, "total_revenue": 0.0})
                performance_data_str += f"ID: {product.shopify_product_id}, Title: {product.title}, Units Sold: {data['units_sold']}, Revenue: ${data['total_revenue']:.2f}\n"

            prompt = f"""
            Analyze the following e-commerce sales data for the last {time_period_days} days.
            Based on units sold and revenue, categorize each product into one of four groups: 'Winner', 'Dud', 'Hidden Gem', or 'Average'.
            - 'Winner': High sales and high revenue.
            - 'Dud': Very low or zero sales.
            - 'Hidden Gem': Moderate potential but low sales, could benefit from marketing.
            - 'Average': All other products.

            Then, provide a concise, actionable summary for the merchant. Identify common themes among winners and suggest specific actions for duds and hidden gems.

            Sales Data:
            ---
            {performance_data_str}
            ---
            Respond in the following format, with one line per product, then the summary:
            [PRODUCT_ID]: [CATEGORY]
            [PRODUCT_ID]: [CATEGORY]
            ---
            Summary: [Your actionable summary here]
            """

            # 4. Get AI insights
            ai_response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1000,
            )
            response_text = ai_response.choices[0].message.content.strip()

            # 5. Parse response and update database
            parts = response_text.split("---")
            category_lines = parts[0].strip().split('\n')
            summary = parts[1].strip().replace("Summary: ", "") if len(parts) > 1 else ""

            product_map = {p.shopify_product_id: p for p in products}

            for line in category_lines:
                try:
                    product_id_str, category = line.split(': ')
                    if product_id_str in product_map:
                        product_to_update = product_map[product_id_str]
                        product_to_update.performance_category = category.strip()
                        product_to_update.ai_performance_summary = summary # Store the same summary for all
                except ValueError:
                    logger.warning(f"Could not parse AI response line: {line}")

            self.db.commit()
            logger.info(f"Successfully completed product performance analysis for shop {shop_id}.")

        except Exception as e:
            logger.error(f"An unexpected error occurred during performance analysis for shop {shop_id}: {e}", exc_info=True)
            self.db.rollback()

    async def run_content_audit(self, product_id: int):
        """
        Runs a content health audit on a single product.

        Args:
            product_id (int): The ID of the product to audit.
        """
        logger.info(f"Starting content audit for product ID {product_id}.")
        try:
            product = self.get_product(product_id)
            if not product.body_html:
                logger.info(f"Product {product_id} has no description. Skipping audit.")
                return

            findings = []
            # The audit checks are run concurrently for maximum efficiency.
            audit_tasks = [
                self._check_broken_links(product),
                self._check_placeholder_text(product),
                self._check_outdated_info(product),
            ]
            results = await asyncio.gather(*audit_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    findings.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"An error occurred during content audit for product {product_id}: {result}", exc_info=result)

            if findings:
                logger.info(f"Found {len(findings)} issues for product {product_id}.")
                product.status = ProductStatus.NEEDS_ATTENTION
                product.audit_findings = "\n".join(findings)
            else:
                # If no findings, ensure status is synced (if it was previously needs_attention)
                if product.status == ProductStatus.NEEDS_ATTENTION:
                    product.status = ProductStatus.SYNCED
                    product.audit_findings = None

            self.db.commit()

        except HTTPException as e:
            # This can happen if get_product fails to find the product.
            logger.warning(f"Could not run audit for product {product_id}: {e.detail}")
        except Exception as e:
            logger.error(f"Unexpected error during content audit for product {product_id}: {e}", exc_info=True)
            self.db.rollback()

    async def _check_broken_links(self, product: Product) -> List[str]:
        """
        Checks for broken links in product body_html concurrently.
        """
        soup = BeautifulSoup(product.body_html, "html.parser")
        links = [link["href"] for link in soup.find_all("a", href=True) if link["href"].startswith(('http://', 'https://'))]

        if not links:
            return []

        async def check_url(url: str):
            try:
                async with self._http_client as client:
                    response = await client.head(url, follow_redirects=True)
                    if response.is_client_error or response.is_server_error:
                        return f"Broken link found: {url} (Status: {response.status_code})"
            except httpx.RequestError as e:
                return f"Link check failed: {url} (Error: {e.__class__.__name__})"
            return None

        tasks = [check_url(url) for url in links]
        results = await asyncio.gather(*tasks)

        return [finding for finding in results if finding is not None]

    async def _check_placeholder_text(self, product: Product) -> List[str]:
        """
        Checks for common placeholder text using regex for better matching.
        This is an async method to maintain consistency with other audit checks.
        """
        findings = []
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, product.body_html, re.IGNORECASE):
                findings.append(f"Placeholder text found: '{pattern}'")
        return findings

    async def _check_outdated_info(self, product: Product) -> List[str]:
        """
        Uses AI to check for outdated information, with robust error handling.
        """
        current_year = datetime.now().year
        prompt = f"""
        Analyze the following product description to identify any time-sensitive language that is now outdated.
        The current year is {current_year}.
        Look for phrases referring to past years (e.g., '2023', '{current_year - 1}'), past holidays, or specific dates that have already passed.
        For example, 'New for 2023' or 'Christmas special from last year' are outdated.
        If you find any outdated information, respond with the specific phrase. If not, respond with 'None'.

        Description:
        ---
        {product.body_html}
        ---
        Outdated phrases (one per line, or 'None'):
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,  # Use model from settings
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            ai_findings = response.choices[0].message.content.strip()
            if ai_findings and ai_findings.lower() != "none":
                return [f"Potentially outdated info: '{finding}'" for finding in ai_findings.split('\n') if finding]
        except APIError as e:
            logger.error(f"OpenAI API error during outdated info check for product {product.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in _check_outdated_info for product {product.id}: {e}", exc_info=True)

        return []

    def create_product(self, product_data: ProductCreate, user_id: int) -> Product:
        """
        Creates a new product in the database.

        Args:
            product_data (ProductCreate): The data for the new product.
            user_id (int): The ID of the user performing the action.

        Returns:
            Product: The newly created product.
        """
        logger.info("Creating a new product.")
        # Business logic before creating the product can be added here.
        # For example, validation, data transformation, etc.
        new_product = product_crud.create_product(self.db, product_data)

        self.audit_log_service.log(
            user_id=user_id,
            action="create_product",
            target_entity="product",
            target_id=new_product.id,
            change_details={"new_data": product_data.dict()},
        )

        return new_product

    def get_product(self, product_id: int) -> Product:
        """
        Retrieves a single product by its ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Raises:
            HTTPException: If the product with the given ID is not found.

        Returns:
            Product: The retrieved product.
        """
        logger.info(f"Fetching product with ID {product_id}.")
        product = product_crud.get_product(self.db, product_id=product_id)
        if not product:
            logger.warning(f"Product with ID {product_id} not found.")
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    def list_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Retrieves a list of products with pagination.

        Args:
            skip (int): The number of products to skip.
            limit (int): The maximum number of products to return.

        Returns:
            List[Product]: A list of products.
        """
        logger.info(f"Listing products with skip={skip}, limit={limit}")
        return product_crud.get_products(self.db, skip=skip, limit=limit)

    def update_product(
        self, product_id: int, product_update: ProductUpdate, user_id: int
    ) -> Product:
        """
        Updates an existing product in the database.

        Args:
            product_id (int): The ID of the product to update.
            product_update (ProductUpdate): The data to update the product with.
            user_id (int): The ID of the user performing the action.

        Raises:
            HTTPException: If the product with the given ID is not found.

        Returns:
            Product: The updated product.
        """
        logger.info(f"Updating product with ID {product_id}.")
        db_product = self.get_product(product_id)
        if not db_product:
            # This case should ideally not be hit if called from a valid endpoint,
            # but it's a crucial safeguard.
            raise HTTPException(status_code=404, detail="Product not found")

        # For audit logging, it's better to capture the state *before* any changes.
        original_data = ProductSchema.from_orm(db_product).dict()

        # Create a content version only if the content is actually changing.
        if product_update.body_html and product_update.body_html != db_product.body_html:
            self.content_version_service.create_version_from_product(
                db_product, user_id, reason="Product Update"
            )

        updated_product = product_crud.update_product(
            self.db, db_obj=db_product, obj_in=product_update
        )

        # Log the change with a clear before/after state.
        change_details = {
            "before": original_data,
            "after": product_update.dict(exclude_unset=True),
        }

        # Avoid logging empty changes
        if change_details["before"] != change_details["after"]:
            self.audit_log_service.log(
                user_id=user_id,
                action="update_product",
                target_entity="product",
                target_id=product_id,
                change_details=change_details,
            )

        return updated_product

    def delete_product(self, product_id: int) -> Optional[Product]:
        """
        Deletes a product from the database.

        Args:
            product_id (int): The ID of the product to delete.

        Returns:
            Optional[Product]: The deleted product, or None if deletion failed unexpectedly.

        Raises:
            HTTPException: If the product with the given ID is not found.
        """
        logger.info(f"Deleting product with ID {product_id}.")
        # Add any business logic here before deleting the product
        # For example, checking for dependencies, etc.
        deleted_product = product_crud.delete_product(self.db, product_id=product_id)
        if not deleted_product:
            logger.warning(
                f"Product with ID {product_id} not found or deletion failed."
            )

        return deleted_product

    async def generate_related_product_recommendations(self, product_id: int):
        """
        Generates and stores a list of related products using AI.
        """
        logger.info(f"Generating related product recommendations for product {product_id}.")
        try:
            target_product = self.get_product(product_id)

            # 1. Fetch all products from the local database to serve as the candidate pool.
            all_products = self.list_products(limit=1000) # Limiting to 1000 for performance

            # Format the candidate list for the AI prompt
            candidate_list = "\n".join([f"ID: {p.shopify_product_id}, Title: {p.title}" for p in all_products if p.id != target_product.id])

            prompt = f"""
            Here is a target product:
            - Title: {target_product.title}
            - Description: {target_product.body_html[:500]}

            Here is a list of other products in the store:
            {candidate_list}

            Analyze the target product and identify the top 5 most complementary or similar products from the list.
            Return only a comma-separated list of the Shopify Product IDs for the 5 recommended products. Example: 123,456,789
            """

            # 2. Call AI to get recommendations
            ai_response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            recommended_ids_str = ai_response.choices[0].message.content.strip()
            recommended_ids = [pid.strip() for pid in recommended_ids_str.split(',')]

            # 3. Store the recommendations in a Shopify Metafield
            # The metafield should be defined in Shopify first (e.g., namespace="custom", key="related_products")
            metafield_payload = {
                "metafield": {
                    "namespace": "custom",
                    "key": "related_products",
                    "value": ",".join(recommended_ids),
                    "type": "product_reference_list", # This type requires the GIDs
                }
            }

            # To use product_reference_list, we need GIDs. This is a simplified example.
            # For a real implementation, you'd convert Shopify IDs to GIDs.
            # For now, we'll store as a simple string.
            metafield_payload["metafield"]["type"] = "single_line_text_field"
            metafield_payload["metafield"]["value"] = ",".join(recommended_ids)


            metafield_url = f"{self.shopify_base_url}/products/{target_product.shopify_product_id}/metafields.json"
            response = await self._http_client.post(metafield_url, headers=self.shopify_headers, json=metafield_payload)
            response.raise_for_status()

            logger.info(f"Successfully stored related product recommendations for product {product_id}.")

        except Exception as e:
            logger.error(f"An unexpected error occurred in generate_related_product_recommendations for product {product_id}: {e}", exc_info=True)

    async def generate_alt_text_for_product_images(self, product_id: int):
        """
        Generates alt-text for product images that are missing it, using a multimodal AI.
        """
        logger.info(f"Starting alt-text generation for product {product_id}.")
        try:
            product = self.get_product(product_id)
            images_url = f"{self.shopify_base_url}/products/{product.shopify_product_id}/images.json"

            response = await self._http_client.get(images_url, headers=self.shopify_headers)
            response.raise_for_status()
            images = response.json().get("images", [])

            for image in images:
                if not image.get("alt"):
                    logger.info(f"Image {image['id']} for product {product_id} is missing alt-text. Generating...")

                    prompt = {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this product image. Write a concise, descriptive alt-text for SEO and accessibility. Include relevant keywords based on the image content."},
                            {"type": "image_url", "image_url": {"url": image["src"]}},
                        ],
                    }

                    try:
                        ai_response = await self.openai_client.chat.completions.create(
                            model=settings.OPENAI_VISION_MODEL_NAME,  # e.g., "gpt-4-vision-preview"
                            messages=[prompt],
                            max_tokens=50,
                        )
                        new_alt_text = ai_response.choices[0].message.content.strip().replace('"', '')

                        # Update the image in Shopify
                        update_url = f"{self.shopify_base_url}/products/{product.shopify_product_id}/images/{image['id']}.json"
                        payload = {"image": {"id": image["id"], "alt": new_alt_text}}
                        update_response = await self._http_client.put(update_url, headers=self.shopify_headers, json=payload)
                        update_response.raise_for_status()
                        logger.info(f"Successfully updated alt-text for image {image['id']} to '{new_alt_text}'.")

                    except APIError as e:
                        logger.error(f"OpenAI API error during alt-text generation for image {image['id']}: {e}")
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Shopify API error updating alt-text for image {image['id']}: {e.response.text}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch images for product {product_id}: {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in generate_alt_text_for_product_images for product {product_id}: {e}", exc_info=True)

    async def update_product_description_in_shopify(
        self, product_id: int, new_description: str
    ) -> ProductSchema:
        """
        Updates a product's description in Shopify and syncs it with the local DB.

        Args:
            product_id (int): The ID of the product to update.
            new_description (str): The new HTML description for the product.

        Returns:
            ProductSchema: The updated product data from Shopify.
        """
        update_url = f"{self.shopify_base_url}/products/{product_id}.json"
        payload = {"product": {"id": product_id, "body_html": new_description}}

        try:
            logger.info(f"Updating description for Shopify product {product_id}")
            response = await self._http_client.put(
                update_url, headers=self.shopify_headers, json=payload
            )
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            updated_product_data = (await response.json()).get("product")
            if not updated_product_data:
                logger.error("Shopify API did not return product data on update.")
                raise HTTPException(
                    status_code=502, detail="Invalid response from Shopify API."
                )

            updated_shopify_product = ProductSchema.model_validate(updated_product_data)

            # Sync the update with the local database
            self.update_product(
                product_id=product_id,
                product_update=ProductUpdate(
                    body_html=updated_shopify_product.body_html
                ),
                user_id=0,  # System action
            )
            logger.info(f"Synced description for product {product_id} in local DB.")

            return updated_shopify_product

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error updating Shopify product {product_id}: {e.response.status_code} - {e.response.text}"
            )
            # Re-raise to be handled by the router
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.json()
            )
        except httpx.RequestError as e:
            logger.error(
                f"Request error while updating Shopify product {product_id}: {e}"
            )
            raise HTTPException(
                status_code=503,
                detail="Service unavailable: Could not connect to Shopify.",
            )
