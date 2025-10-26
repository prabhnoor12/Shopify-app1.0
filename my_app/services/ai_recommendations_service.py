import logging
import json
from functools import lru_cache
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed
from ..models.shop import ShopifyUser
from ..services.shop_service import ShopifyService

logger = logging.getLogger(__name__)


class AIRecommendationsService:
    def __init__(self, openai_client: OpenAI, shopify_service: ShopifyService):
        self._openai_client = openai_client
        self._shopify_service = shopify_service

    @lru_cache(maxsize=128)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_test_recommendations(
        self, user: ShopifyUser, product_id: int
    ) -> list[dict]:
        """
        Analyzes a product and suggests A/B tests for title, description, and price.
        """
        product = self._shopify_service.get_product(user, product_id)
        if not product:
            raise ValueError("Product not found")

        # Extracting price from variants
        price = "Not available"
        if product.get("variants"):
            price = product["variants"][0].get("price", "Not available")

        prompt = f"""
        Analyze the following Shopify product and suggest 3 diverse, high-impact A/B testing ideas to improve its conversion rate.
        For each idea, provide a 'name', a 'description', and a 'type' ('title', 'description', or 'price').
        Focus on tangible, actionable tests.

        Product Title: {product.get("title", "")}
        Product Description: {product.get("body_html", "")}
        Product Type: {product.get("product_type", "")}
        Vendor: {product.get("vendor", "")}
        Tags: {product.get("tags", "")}
        Price: {price}

        Return the response as a valid JSON array of objects.
        Example:
        [
            {{"name": "Test Emotional vs. Functional Title", "description": "Test a title focused on benefits versus a title focused on features.", "type": "title"}},
            {{"name": "Test Scarcity in Description", "description": "Create a variant that adds a sense of urgency or scarcity to the product description.", "type": "description"}},
            {{"name": "Test a 5% Price Reduction", "description": "Test if a small price reduction increases overall revenue.", "type": "price"}}
        ]
        """

        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are an A/B testing expert for Shopify, providing recommendations in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            # The response content is a JSON string that needs to be parsed.
            # The API returns a JSON object, and the actual list is a value within it.
            # Let's assume the response is `{"recommendations": [...]}` or similar, we need to find the list.
            json_response = json.loads(response.choices[0].message.content)

            # Find the first value in the parsed JSON that is a list.
            for value in json_response.values():
                if isinstance(value, list):
                    return value

            logger.error("No list found in the JSON response from OpenAI.")
            return []

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(
                f"Error decoding or parsing test recommendations from OpenAI: {e}"
            )
            return []
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while getting test recommendations: {e}"
            )
            return []

    @lru_cache(maxsize=128)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_variants(
        self,
        user: ShopifyUser,
        product_id: int,
        test_recommendation: dict,
        num_variants: int = 2,
    ) -> list[dict]:
        """
        Generates content for variants based on a specific test recommendation.
        The generated content can be for 'title', 'description', or 'price'.
        """
        product = self._shopify_service.get_product(user, product_id)
        if not product:
            raise ValueError("Product not found")

        test_type = test_recommendation.get("type", "description")
        test_description = test_recommendation.get("description", "")

        # Extracting current values
        current_title = product.get("title", "")
        current_description = product.get("body_html", "")
        current_price = "0.00"
        if product.get("variants"):
            current_price = product["variants"][0].get("price", "0.00")

        prompt = f"""
        You are an expert copywriter and pricing strategist for e-commerce.
        Based on the Shopify product below and the A/B test idea, generate {num_variants} new variants.
        The 'type' of the test is '{test_type}'.

        **Product Details:**
        - Title: {current_title}
        - Description: {current_description}
        - Price: {current_price}

        **A/B Test Idea:** {test_description}

        Generate {num_variants} variants for the '{test_type}'.
        - If type is 'title', return new titles.
        - If type is 'description', return new, complete product descriptions.
        - If type is 'price', return new price points as strings.

        Return a valid JSON object with a single key "variants" holding a list of strings.
        Example for a 'title' test:
        {{"variants": ["New Title 1", "New Title 2"]}}
        Example for a 'price' test:
        {{"variants": ["28.99", "27.50"]}}
        """

        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert copywriter and pricing strategist providing JSON output.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            json_response = json.loads(response.choices[0].message.content)
            variants = json_response.get("variants", [])

            if isinstance(variants, list) and all(isinstance(v, str) for v in variants):
                # Return a list of dictionaries to be consistent and more descriptive
                return [{"content": v, "type": test_type} for v in variants]

            logger.error(
                "Generated variants from OpenAI are not in the expected format."
            )
            return []
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(
                f"Error decoding or parsing generated variants from OpenAI: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while generating variants: {e}")
            return []
