import asyncio
from typing import Dict, Any
import httpx
import logging
from sqlalchemy.orm import Session
import geoip2.database
import time

from ..models.shop import ShopifyUser
from ..schemas.shop_dynamic import DynamicContentRequest, DynamicContentResponse
from my_app.dependencies.config import settings

logger = logging.getLogger(__name__)

# --- Configuration for Dynamic Snippets ---
# In a real application, this would be stored in a database and managed by the merchant.
LOCATION_SNIPPETS = {
    "GB": {"spelling": "Colour", "shipping": "Free UK Delivery"},
    "US": {"spelling": "Color", "shipping": "Free US Shipping"},
    "CA": {"spelling": "Colour", "shipping": "Free Shipping to Canada"},
    "AU": {"spelling": "Colour", "shipping": "Free Shipping to Australia"},
    "default": {"spelling": "Color", "shipping": "Free Worldwide Shipping"},
}

REFERRAL_SNIPPETS = {
    "techblog.com": "As featured on TechBlog: a breakdown of the cutting-edge specs.",
    "fashionista.com": "Spotted on Fashionista: the must-have style of the season.",
    "google.com": "Welcome! Find the perfect fit recommended by our community.",
}

WEATHER_SNIPPETS = {
    "hot": "It's hot today! Stay cool with our lightweight collection.",
    "warm": "Perfect weather to be out and about. Grab this essential for your day.",
    "cool": "A bit chilly? This will keep you comfortably warm.",
    "cold": "It's cold outside! Stay warm with our premium insulated gear.",
}


class ShopDynamicService:
    """
    Handles real-time personalization of product descriptions on the storefront.
    This service is designed to be robust, efficient, and easily extensible.
    """

    def __init__(self, db: Session):
        self.db = db
        self._http_client = httpx.AsyncClient()
        self.geoip_reader = self._init_geoip_reader()

    def _init_geoip_reader(self):
        """Initializes the GeoIP reader, handling potential errors gracefully."""
        try:
            return geoip2.database.Reader(settings.GEOIP_DATABASE_PATH)
        except FileNotFoundError:
            logger.warning(
                "GeoIP database not found at path: %s. Geolocation features will be disabled.",
                settings.GEOIP_DATABASE_PATH,
            )
            return None

    async def close(self):
        """Close the HTTP client and other resources."""
        await self._http_client.aclose()
        if self.geoip_reader:
            self.geoip_reader.close()

    async def get_dynamic_content(
        self, user: ShopifyUser, request: DynamicContentRequest
    ) -> DynamicContentResponse:
        """
        Orchestrates the generation of dynamic content snippets based on visitor data,
        running independent async operations concurrently for maximum efficiency.
        """
        location_info = self._get_location_info(request.visitor_ip)
        location_snippets = self._get_location_based_snippets(location_info)

        async with asyncio.TaskGroup() as tg:
            inventory_task = tg.create_task(
                self._get_product_inventory(user, request.product_id)
            )
            weather_task = tg.create_task(self._get_weather_data(location_info))

        inventory_level = inventory_task.result()
        weather_info = weather_task.result()

        scarcity_snippet = self._get_scarcity_snippet(inventory_level)
        referral_snippet = self._get_referral_based_snippet(request.referral_source)
        social_proof_snippet = self._get_social_proof_snippet(request.product_id)
        weather_snippet = self._get_weather_based_snippet(weather_info)

        return DynamicContentResponse(
            location_snippets=location_snippets,
            scarcity_snippet=scarcity_snippet,
            referral_snippet=referral_snippet,
            social_proof_snippet=social_proof_snippet,
            weather_snippet=weather_snippet,
        )

    def _get_location_info(self, ip_address: str) -> Dict[str, Any] | None:
        """Gets geographic information from an IP address."""
        if not self.geoip_reader or not ip_address:
            return None
        try:
            return self.geoip_reader.city(ip_address)
        except geoip2.errors.AddressNotFoundError:
            logger.info("IP address not found in GeoIP database: %s", ip_address)
        except Exception as e:
            logger.error("Error during GeoIP lookup for IP %s: %s", ip_address, e)
        return None

    def _get_location_based_snippets(
        self, location_info: Dict[str, Any] | None
    ) -> dict:
        """Returns personalized text based on the visitor's location."""
        if not location_info:
            return LOCATION_SNIPPETS["default"]

        country_code = location_info.country.iso_code
        return LOCATION_SNIPPETS.get(country_code, LOCATION_SNIPPETS["default"])

    async def _get_weather_data(
        self, location_info: Dict[str, Any] | None
    ) -> Dict[str, Any] | None:
        """
        Fetches weather data for a given location.
        NOTE: In a production environment, cache the results of this function.
        """
        if not location_info or not settings.OPENWEATHER_API_KEY:
            return None

        lat = location_info.location.latitude
        lon = location_info.location.longitude
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.OPENWEATHER_API_KEY}&units=metric"

        try:
            response = await self._http_client.get(weather_url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Failed to fetch weather data: %s", e)
            return None

    def _get_weather_based_snippet(
        self, weather_info: Dict[str, Any] | None
    ) -> str | None:
        """Generates a snippet based on the current weather."""
        if not weather_info or "main" not in weather_info:
            return None

        temp = weather_info["main"].get("temp")
        if temp is None:
            return None

        if temp > 25:
            return WEATHER_SNIPPETS["hot"]
        elif 18 <= temp <= 25:
            return WEATHER_SNIPPETS["warm"]
        elif 10 <= temp < 18:
            return WEATHER_SNIPPETS["cool"]
        else:
            return WEATHER_SNIPPETS["cold"]

    async def _get_product_inventory(
        self, user: ShopifyUser, product_id: int
    ) -> int | None:
        """
        Fetches the total inventory level for a product from Shopify.
        NOTE: In a production environment, cache the results of this function.
        """
        variants_url = f"https://{user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products/{product_id}/variants.json?fields=inventory_quantity"
        headers = {"X-Shopify-Access-Token": user.access_token}

        try:
            response = await self._http_client.get(
                variants_url, headers=headers, timeout=10.0
            )
            response.raise_for_status()
            variants = response.json().get("variants", [])
            if variants:
                return sum(v.get("inventory_quantity", 0) for v in variants)
            return 0
        except httpx.RequestError as e:
            logger.error("Failed to fetch inventory for product %d: %s", product_id, e)
        except Exception as e:
            logger.error(
                "An unexpected error occurred fetching inventory for product %d: %s",
                product_id,
                e,
            )
        return None

    def _get_scarcity_snippet(self, inventory_level: int | None) -> str | None:
        """Generates a scarcity message if inventory is low."""
        if (
            inventory_level is not None
            and 0 < inventory_level <= settings.SCARCITY_THRESHOLD
        ):
            return f"Selling fast! Only {inventory_level} left in stock."
        return None

    def _get_referral_based_snippet(self, referral_source: str | None) -> str | None:
        """Returns a snippet based on the referral source domain."""
        if not referral_source:
            return None

        for domain, snippet in REFERRAL_SNIPPETS.items():
            if domain in referral_source:
                return snippet
        return None

    def _get_social_proof_snippet(self, product_id: int) -> str | None:
        """
        Generates a realistic, time-sensitive social proof message.
        NOTE: This simulates a real-time analytics system. In production, this
        would be replaced by a call to a service like Redis or a database
        that tracks actual user events.
        """
        # Simulate a base number of viewers based on product ID
        base_viewers = (product_id % 50) + 5
        # Add a time-based sine wave to simulate daily traffic fluctuations
        # This creates a more realistic, non-random pattern
        time_component = int(
            5 * (1 + time.time() % 600 / 600)
        )  # Fluctuates over 10 mins

        viewers_now = base_viewers + time_component

        return f"{viewers_now} people are viewing this right now."
