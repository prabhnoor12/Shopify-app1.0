import httpx
import logging
import datetime
import json
from typing import Dict, List, Any, Callable
from functools import wraps
from sqlalchemy.orm import Session
from openai import OpenAI, APIError, RateLimitError, AuthenticationError
from fastapi import HTTPException, status
import jinja2
from bs4 import BeautifulSoup
import re
from datetime import timezone

from ..models.shop import ShopifyUser
from ..models.brand_voice import BrandVoice
from ..schemas.shop import (
    GenerateRequest,
    SaveRequest,
    GenerateResponse,
    BulkSaveRequest,
    BulkSaveResponse,
    BulkGenerateRequest,
    BulkGenerateResponse,
    RegenerateVariantRequest,
    GenerateFromImageRequest,
    GenerateFromUrlRequest,
    BenefitOrientedRequest,
    BenefitOrientedResponse,
    BulkFindReplaceRequest,
    BulkFindReplaceResponse,
)
from my_app.utils.string import slugify
from ..services import seo_service
from my_app.utils.decorators import retry_sync
from my_app.middleware.logging import logger
from ..core.config import settings


class ShopifyService:
    """
    Service for handling Shopify-related business logic, including AI-powered
    content generation, SEO analysis, and usage tracking.
    """

    def __init__(self, db: Session, openai_client: OpenAI, http_client_):
        self.db = db
        self.openai_client = openai_client
        self._http_client = http_client_
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("my_app/templates/prompts"),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

    def _is_on_trial(self, user: ShopifyUser) -> bool:
        """
        Checks if a user is currently on trial, handling timezone-aware comparison.
        """
        if not user.trial_ends_at:
            return False

        trial_ends_at = user.trial_ends_at
        # Ensure the datetime is timezone-aware for comparison
        if trial_ends_at.tzinfo is None:
            trial_ends_at = trial_ends_at.replace(tzinfo=timezone.utc)

        return trial_ends_at > datetime.datetime.now(timezone.utc)

    def _get_brand_voice_prompt(self, user: ShopifyUser) -> str:
        """
        Generates a brand voice prompt string based on the user's settings.
        """
        brand_voice = (
            self.db.query(BrandVoice).filter(BrandVoice.shop_id == user.id).first()
        )
        if not brand_voice:
            return ""

        prompt_lines = ["Please adhere to the following brand guidelines:"]
        if brand_voice.tone_of_voice:
            prompt_lines.append(f"- Tone of voice: {brand_voice.tone_of_voice}")
        if brand_voice.vocabulary_preferences:
            preferred = brand_voice.vocabulary_preferences.get("preferred", [])
            avoid = brand_voice.vocabulary_preferences.get("avoid", [])
            if preferred:
                prompt_lines.append(f"- Preferred vocabulary: {', '.join(preferred)}")
            if avoid:
                prompt_lines.append(f"- Avoid using: {', '.join(avoid)}")
        if brand_voice.industry_jargon:
            prompt_lines.append(
                f"- Industry jargon to use: {', '.join(brand_voice.industry_jargon)}"
            )
        if brand_voice.banned_words:
            prompt_lines.append(
                f"- Banned words: {', '.join(brand_voice.banned_words)}"
            )

        if len(prompt_lines) > 1:
            return "\n".join(prompt_lines)
        return ""

    def close(self):
        """Close the HTTP client."""
        self._http_client.close()

    @retry_sync
    def fetch_products(self, user: ShopifyUser) -> List[Dict[str, Any]]:
        """
        Fetches and normalizes a list of all products from the Shopify store,
        handling pagination.
        """
        all_products = []
        products_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products.json?limit=250"
        headers = {"X-Shopify-Access-Token": user.access_token}

        while products_url:
            try:
                response = self._http_client.get(
                    products_url, headers=headers, timeout=settings.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                products_data = response.json().get("products", [])
                all_products.extend(products_data)

                # Handle Shopify's cursor-based pagination
                link_header = response.headers.get("Link")
                products_url = None  # Assume no next page unless found
                if link_header:
                    links = link_header.split(", ")
                    for link in links:
                        if 'rel="next"' in link:
                            # Extract URL from <...>
                            products_url = link[link.find("<") + 1 : link.find(">")]
                            break
            except httpx.RequestError as e:
                logger.error("Failed to fetch a page of products: %s", e)
                # Decide if you want to stop or continue. For now, we stop.
                break

        logger.info(
            "Successfully fetched %d products for shop: %s",
            len(all_products),
            user.shop_domain,
        )
        return [
            {
                "id": p["id"],
                "title": p["title"],
                "slug": slugify(p["title"]),
                "tags": p.get("tags", ""),
                "product_type": p.get("product_type", ""),
            }
            for p in all_products
        ]

    @retry_sync
    def fetch_orders_for_product(
        self, user: ShopifyUser, product_id: int
    ) -> List[Dict[str, Any]]:
        """
        Fetches a list of orders for a specific product from the Shopify store.
        """
        orders_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products/{product_id}/orders.json"
        headers = {"X-Shopify-Access-Token": user.access_token}

        response = self._http_client.get(
            orders_url, headers=headers, timeout=settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        orders_data = response.json().get("orders", [])

        logger.info(
            "Successfully fetched %d orders for product %d for shop: %s",
            len(orders_data),
            product_id,
            user.shop_domain,
        )
        return orders_data

    @retry_sync
    def generate_description(
        self, user: ShopifyUser, request: GenerateRequest
    ) -> GenerateResponse:
        """
        Generates multiple product descriptions and keywords using OpenAI,
        supports brand voice training, and manages usage limits.
        Now includes SEO analysis and suggestions.
        """
        is_on_trial = self._is_on_trial(user)

        if (
            not is_on_trial
            and user.generations_used >= settings.MONTHLY_GENERATION_LIMIT
        ):
            logger.warning(
                "Monthly generation limit exceeded for user: %s", user.shop_domain
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly generation limit exceeded.",
            )

        # --- Refactored Prompt Generation ---
        # Start with the base request context
        prompt_context = request.model_dump()

        # Always apply the brand voice
        prompt_context["brand_voice_prompt"] = self._get_brand_voice_prompt(user)

        # Add persona as a premium feature
        is_premium = not is_on_trial and user.plan.lower() != "free"
        if request.persona and is_premium:
            prompt_context["persona"] = request.persona

        template = self.jinja_env.get_template("product_description.jinja2")
        prompt = template.render(**prompt_context)
        # --- End of Refactored Prompt Generation ---

        response = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            n=request.num_variants,
            response_format={"type": "json_object"},
        )

        descriptions = []
        keywords = []
        meta_title = None
        meta_description = None

        for i, choice in enumerate(response.choices):
            parsed_content = self._parse_generation_choice(choice)
            descriptions.append(parsed_content["description"])
            if i == 0:  # Only take seo fields from the first variant
                keywords = parsed_content["keywords"]
                meta_title = parsed_content["meta_title"]
                meta_description = parsed_content["meta_description"]

        # --- New SEO Analysis Step ---
        seo_analysis_results = None
        seo_suggestions = None
        primary_keyword = (
            request.keywords[0]
            if request.keywords
            else (keywords[0] if keywords else "")
        )

        if primary_keyword and descriptions:
            # Run analysis on the first generated description
            analysis = seo_service.analyze_seo(
                primary_keyword=primary_keyword,
                title=request.title,
                description=descriptions[0],
                meta_title=meta_title,
                meta_description=meta_description,
            )
            seo_analysis_results = analysis

            # Generate AI suggestions based on the analysis
            suggestions = seo_service.generate_seo_improvement_suggestions(
                openai_client=self.openai_client,
                analysis_results=analysis,
                primary_keyword=primary_keyword,
                title=request.title,
                description=descriptions[0],
            )
            seo_suggestions = suggestions
        # --- End of New SEO Analysis Step ---

        # update and commit usage count
        user.generations_used += request.num_variants
        self.db.add(user)
        self.db.commit()
        logger.info(
            "Successfully generated %d descriptions and updated usage for user: %s",
            len(descriptions),
            user.shop_domain,
        )
        return GenerateResponse(
            descriptions=descriptions,
            keywords=keywords,
            meta_title=meta_title,
            meta_description=meta_description,
            seo_analysis=seo_analysis_results,
            seo_suggestions=seo_suggestions,
        )

    @retry_sync
    def generate_description_from_image(
        self, user: ShopifyUser, request: GenerateFromImageRequest
    ) -> GenerateResponse:
        """
        Generates a product description from an image URL using OpenAI Vision.
        """
        is_on_trial = self._is_on_trial(user)
        if (
            not is_on_trial
            and user.generations_used >= settings.MONTHLY_GENERATION_LIMIT
        ):
            logger.warning(
                "Monthly generation limit exceeded for user: %s", user.shop_domain
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly generation limit exceeded.",
            )

        template = self.jinja_env.get_template("image_description.jinja2")
        prompt = template.render(request=request.model_dump())

        response = self.openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": request.image_url},
                        },
                    ],
                }
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            n=request.num_variants,
            response_format={"type": "json_object"},
        )

        descriptions = []
        keywords = []
        meta_title = None
        meta_description = None

        for i, choice in enumerate(response.choices):
            parsed_content = self._parse_generation_choice(choice)
            descriptions.append(parsed_content["description"])
            if i == 0:  # Only take seo fields from the first variant
                keywords = parsed_content["keywords"]
                meta_title = parsed_content["meta_title"]
                meta_description = parsed_content["meta_description"]

        user.generations_used += request.num_variants
        self.db.add(user)
        self.db.commit()
        logger.info(
            "Successfully generated %d descriptions from image for user: %s",
            len(descriptions),
            user.shop_domain,
        )
        return GenerateResponse(
            descriptions=descriptions,
            keywords=keywords,
            meta_title=meta_title,
            meta_description=meta_description,
        )

    @retry_sync
    def save_description(self, user: ShopifyUser, request: SaveRequest) -> None:
        """
        Updates the product description on Shopify.
        """
        product_update_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products/{request.product_id}.json"
        headers = {
            "X-Shopify-Access-Token": user.access_token,
            "Content-Type": "application/json",
        }
        payload = {
            "product": {"id": request.product_id, "body_html": request.new_description}
        }

        response = self._http_client.put(
            product_update_url,
            headers=headers,
            json=payload,
            timeout=settings.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        logger.info(
            "Successfully updated product %d for shop: %s",
            request.product_id,
            user.shop_domain,
        )

    @retry_sync
    def bulk_save_descriptions(
        self, user: ShopifyUser, request: BulkSaveRequest
    ) -> BulkSaveResponse:
        """
        Updates multiple product descriptions on Shopify sequentially.
        """
        success = []
        errors = []
        product_ids = [req.product_id for req in request.requests]
        for i, save_request in enumerate(request.requests):
            try:
                self.save_description(user, save_request)
                success.append(product_ids[i])
                time.sleep(0.2)  # Add a small delay to avoid hitting rate limits
            except Exception as e:
                logger.error(
                    "Error saving description in bulk for product %d: %s",
                    product_ids[i],
                    e,
                )
                errors.append(product_ids[i])

        return BulkSaveResponse(success=success, errors=errors)

    @retry_sync
    def bulk_generate_descriptions(
        self, user: ShopifyUser, request: BulkGenerateRequest
    ) -> BulkGenerateResponse:
        """
        Generates multiple product descriptions in bulk sequentially.
        """
        successful_results = []
        errors = []
        product_ids = [product.product_id for product in request.products]
        for i, product in enumerate(request.products):
            try:
                generate_request = GenerateRequest(
                    product_id=product.product_id,
                    title=product.title,
                    tone=request.tone,
                    length=request.length,
                    style=request.style,
                    keywords=request.keywords,
                    brand_voice_examples=request.brand_voice_examples,
                    num_variants=request.num_variants,
                )
                result = self.generate_description(user, generate_request)
                successful_results.append(result)
            except Exception as e:
                logger.error(
                    "Error generating description in bulk for product %d: %s",
                    product_ids[i],
                    e,
                )
                errors.append(product_ids[i])

        return BulkGenerateResponse(results=successful_results, errors=errors)

    @retry_sync
    def generate_description_from_url(
        self, user: ShopifyUser, request: GenerateFromUrlRequest
    ) -> GenerateResponse:
        """
        Generates a product description by scraping a URL.
        """
        is_on_trial = self._is_on_trial(user)
        if (
            not is_on_trial
            and user.generations_used >= settings.MONTHLY_GENERATION_LIMIT
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly generation limit exceeded.",
            )

        # 1. Crawl the source page
        try:
            response = self._http_client.get(
                request.url, timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            logger.error("Failed to fetch URL %s: %s", request.url, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch content from the provided URL: {e}",
            )

        # 2. Extract key information
        soup = BeautifulSoup(response.text, "html.parser")
        # Get all text from the body, which is a simple but effective starting point
        scraped_text = soup.body.get_text(separator=" ", strip=True)

        # Limit the text to avoid overly long prompts
        max_scraped_length = 3000  # Approx 750 tokens
        if len(scraped_text) > max_scraped_length:
            scraped_text = scraped_text[:max_scraped_length]

        # 3. Rewrite the content using the store's unique Brand Voice
        prompt_context = {
            "scraped_text": scraped_text,
            "request": request.model_dump(),
        }

        brand_voice_prompt = self._get_brand_voice_prompt(user)

        prompt_context["brand_voice_prompt"] = brand_voice_prompt

        template = self.jinja_env.get_template("url_description.jinja2")
        prompt = template.render(prompt_context)

        # 4. Generate response with OpenAI
        response = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            n=request.num_variants,
            response_format={"type": "json_object"},
        )

        descriptions = []
        keywords = []
        meta_title = None
        meta_description = None

        for i, choice in enumerate(response.choices):
            parsed_content = self._parse_generation_choice(choice)
            descriptions.append(parsed_content["description"])
            if i == 0:  # Only take seo fields from the first variant
                keywords = parsed_content["keywords"]
                meta_title = parsed_content["meta_title"]
                meta_description = parsed_content["meta_description"]

        # Update usage count
        user.generations_used += request.num_variants
        self.db.add(user)
        self.db.commit()

        logger.info(
            "Successfully generated %d descriptions from URL for user: %s",
            len(descriptions),
            user.shop_domain,
        )

        return GenerateResponse(
            descriptions=descriptions,
            keywords=keywords,
            meta_title=meta_title,
            meta_description=meta_description,
        )

    @retry_sync
    def regenerate_variant(
        self, user: ShopifyUser, request: RegenerateVariantRequest
    ) -> GenerateResponse:
        """
        Regenerates a single product description variant based on user feedback.
        """
        is_on_trial = self._is_on_trial(user)
        if (
            not is_on_trial
            and user.generations_used >= settings.MONTHLY_GENERATION_LIMIT
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly generation limit exceeded.",
            )

        template = self.jinja_env.get_template("regenerate_variant.jinja2")
        prompt = template.render(
            title=request.title,
            original_description=request.original_description,
            feedback=request.feedback,
            brand_voice_prompt=self._get_brand_voice_prompt(user),
        )

        response = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            n=1,  # We only generate one variant for regeneration
            response_format={"type": "json_object"},
        )

        # Since we expect only one choice, we can directly parse it.
        if not response.choices:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI failed to generate a response.",
            )

        parsed_content = self._parse_generation_choice(response.choices[0])

        # Update usage count
        user.generations_used += 1
        self.db.add(user)
        self.db.commit()

        logger.info(
            "Successfully regenerated a variant for product %d for user: %s",
            request.product_id,
            user.shop_domain,
        )

        return GenerateResponse(
            descriptions=[parsed_content["description"]],
            keywords=parsed_content["keywords"],
            meta_title=parsed_content["meta_title"],
            meta_description=parsed_content["meta_description"],
        )

    @retry_sync
    def transform_feature_to_benefit(
        self, user: ShopifyUser, request: BenefitOrientedRequest
    ) -> BenefitOrientedResponse:
        """
        Transforms a product feature into a customer-centric benefit using AI.
        """
        is_on_trial = self._is_on_trial(user)
        if (
            not is_on_trial
            and user.generations_used >= settings.MONTHLY_GENERATION_LIMIT
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly generation limit exceeded.",
            )

        template = self.jinja_env.get_template("feature_to_benefit.jinja2")
        prompt = template.render(
            product_name=request.product_name,
            feature=request.feature,
            brand_voice_prompt=self._get_brand_voice_prompt(user),
        )

        response = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,  # Benefits are usually shorter
            temperature=0.7,  # Keep it creative but focused
            n=1,
            response_format={"type": "json_object"},
        )

        if not response.choices:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI failed to generate a response.",
            )

        try:
            content = json.loads(response.choices[0].message.content)
            benefit_text = content.get("benefit_text", "").strip()
            if not benefit_text:  # Handle case where key exists but is empty
                benefit_text = response.choices[0].message.content.strip()

        except (json.JSONDecodeError, AttributeError):
            logger.error(
                "Failed to parse JSON response from OpenAI for benefit transformation."
            )
            # Fallback to raw content if JSON parsing fails
            benefit_text = response.choices[0].message.content.strip()

        # Update usage count
        user.generations_used += 1
        self.db.add(user)
        self.db.commit()

        logger.info(
            "Successfully transformed feature to benefit for user: %s",
            user.shop_domain,
        )

        return BenefitOrientedResponse(benefit_text=benefit_text)

    @retry_sync
    def bulk_find_and_replace(
        self, user: ShopifyUser, request: BulkFindReplaceRequest
    ) -> BulkFindReplaceResponse:
        """
        Finds and replaces text across multiple product descriptions with support for
        pagination, collection filtering, and case-insensitive whole-word matching.
        """
        updated_products = []
        errors = []
        total_matches = 0

        headers = {"X-Shopify-Access-Token": user.access_token}

        # Determine the initial products URL based on whether a collection ID is provided
        if request.collection_id:
            # Endpoint for products in a specific collection
            base_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/collections/{request.collection_id}/products.json"
        else:
            # Endpoint for all products
            base_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products.json"

        products_url = f"{base_url}?limit=250"

        # Compile regex for replacement
        # \b ensures we match whole words only
        find_regex = re.compile(
            r"\b" + re.escape(request.find_text) + r"\b", re.IGNORECASE
        )

        while products_url:
            try:
                response = self._http_client.get(
                    products_url, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                products = response.json().get("products", [])

                # Iterate over the current page of products and update
                for product in products:
                    product_id = product["id"]
                    description = product.get("body_html", "")

                    # Check if the description contains the text to be replaced using regex
                    if description and find_regex.search(description):
                        # Perform replacement using regex
                        new_description, num_substitutions = find_regex.subn(
                            request.replace_text, description
                        )
                        total_matches += num_substitutions

                        if num_substitutions > 0:
                            try:
                                # Use the existing save_description method
                                save_req = SaveRequest(
                                    product_id=product_id,
                                    new_description=new_description,
                                )
                                self.save_description(user, save_req)
                                updated_products.append(product_id)
                                time.sleep(
                                    0.5
                                )  # Rate limit to avoid overwhelming Shopify's API
                            except Exception as e:
                                errors.append(
                                    {"product_id": product_id, "error": str(e)}
                                )

                # Handle Shopify's cursor-based pagination
                link_header = response.headers.get("Link")
                products_url = None  # Assume no next page unless found
                if link_header:
                    links = link_header.split(", ")
                    for link in links:
                        if 'rel="next"' in link:
                            # Extract URL from <...>
                            products_url = link[link.find("<") + 1 : link.find(">")]
                            break

            except httpx.RequestError as e:
                logger.error("Failed to fetch products for bulk replace: %s", e)
                # Stop pagination on error to avoid infinite loops
                products_url = None
                errors.append(
                    {"product_id": None, "error": f"Failed to fetch product page: {e}"}
                )

        logger.info(
            "Bulk find and replace completed for user %s. Matches: %d, Updated: %d, Errors: %d",
            user.shop_domain,
            total_matches,
            len(updated_products),
            len(errors),
        )

        return BulkFindReplaceResponse(
            updated_products=updated_products,
            errors=errors,
            total_matches=total_matches,
        )

    def _parse_generation_choice(self, choice) -> Dict[str, Any]:
        """
        Parses the content from an OpenAI completion choice, handling potential
        JSON decoding errors.
        """
        try:
            content = json.loads(choice.message.content)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse JSON, falling back to regex.")
            content = self._parse_description_with_regex(choice.message.content)

        # Ensure all expected keys are present
        return {
            "description": content.get("description", "").strip(),
            "keywords": content.get("keywords", []),
            "meta_title": content.get("meta_title", "").strip(),
            "meta_description": content.get("meta_description", "").strip(),
        }

    def _parse_description_with_regex(self, text: str) -> Dict[str, Any]:
        """
        A fallback method to parse the AI's output using regex when JSON parsing fails.
        This is less reliable and should only be used as a backup.
        """
        logger.info("Attempting to parse AI response with regex.")
        description = (
            re.search(r'["\']description["\']:\s*["\'](.*?)["\']', text, re.DOTALL)
            or ""
        )
        keywords_match = re.search(
            r'["\']keywords["\']:\s*\[(.*?)\]', text, re.DOTALL
        )
        meta_title = (
            re.search(r'["\']meta_title["\']:\s*["\'](.*?)["\']', text, re.DOTALL) or ""
        )
        meta_description = (
            re.search(r'["\']meta_description["\']:\s*["\'](.*?)["\']', text, re.DOTALL)
            or ""
        )

        return {
            "description": description.group(1).strip() if description else text,
            "keywords": (
                [kw.strip().strip('"\'') for kw in keywords_match.group(1).split(",")]
                if keywords_match
                else []
            ),
            "meta_title": meta_title.group(1).strip() if meta_title else "",
            "meta_description": (
                meta_description.group(1).strip() if meta_description else ""
            ),
        }
