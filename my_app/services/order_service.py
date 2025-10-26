"""
Service for fetching and processing order data from Shopify.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import httpx
from ..dependencies.config import settings

logger = logging.getLogger(__name__)

class OrderService:
    """
    Encapsulates business logic for fetching and processing Shopify order data.
    """
    def __init__(self):
        self.shopify_api_version = settings.SHOPIFY_API_VERSION
        self.shopify_base_url = f"https://{settings.SHOPIFY_STORE_DOMAIN}/admin/api/{self.shopify_api_version}"
        self.shopify_headers = {
            "X-Shopify-Access-Token": settings.SHOPIFY_ADMIN_API_KEY,
            "Content-Type": "application/json",
        }
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def get_sales_data_for_products(self, time_period_days: int) -> Dict[str, Dict[str, Any]]:
        """
        Fetches order data and calculates sales metrics for each product.
        """
        logger.info(f"Fetching sales data for the last {time_period_days} days.")
        product_sales = {}

        # Calculate the date range
        start_date = (datetime.now() - timedelta(days=time_period_days)).isoformat()

        orders_url = f"{self.shopify_base_url}/orders.json?status=any&created_at_min={start_date}"

        try:
            response = await self._http_client.get(orders_url, headers=self.shopify_headers)
            response.raise_for_status()
            orders = response.json().get("orders", [])

            for order in orders:
                for item in order.get("line_items", []):
                    product_id = str(item.get("product_id"))
                    if not product_id:
                        continue

                    if product_id not in product_sales:
                        product_sales[product_id] = {"units_sold": 0, "total_revenue": 0.0}

                    product_sales[product_id]["units_sold"] += item.get("quantity", 0)
                    product_sales[product_id]["total_revenue"] += float(item.get("price", 0.0)) * item.get("quantity", 0)

            return product_sales

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch orders from Shopify: {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching sales data: {e}", exc_info=True)
            return {}

    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
