import requests
import logging
from typing import Dict, Any, Optional

from ..dependencies.config import get_settings
from ..utils.shopify import is_valid_shop_domain

# --- Configuration & Setup ---
logger = logging.getLogger(__name__)
settings = get_settings()

SHOPIFY_API_VERSION = settings.SHOPIFY_API_VERSION

# --- Powerful & Robust Shopify API Client ---


class ShopifyClient:
    """
    A robust client for interacting with the Shopify REST and GraphQL APIs,
    featuring session management, rate limit handling, and centralized error handling.
    """

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = SHOPIFY_API_VERSION,
    ):
        if not is_valid_shop_domain(shop_domain):
            raise ValueError(f"Invalid Shopify domain provided: {shop_domain}")
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version
        self.rest_base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
        self.graphql_url = (
            f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"
        )
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Creates a requests session with appropriate headers for Shopify API calls."""
        session = requests.Session()
        session.headers.update(
            {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json",
            }
        )
        return session

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handles API response, including rate limits and errors."""
        rate_limit_info = response.headers.get("X-Shopify-Shop-Api-Call-Limit")
        if rate_limit_info:
            used, limit = map(int, rate_limit_info.split("/"))
            if used >= limit * 0.8:
                logger.warning(
                    f"Shopify API rate limit approaching for {self.shop_domain}: {used}/{limit}"
                )

        try:
            response.raise_for_status()
            # Handle cases where response body is empty (e.g., 204 No Content)
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP Error from Shopify API for {self.shop_domain}: {e} - Response: {response.text}"
            )
            raise

    def execute_rest(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Executes a request against the Shopify REST API.
        """
        url = f"{self.rest_base_url}/{endpoint}.json"
        try:
            response = self.session.request(
                method, url, json=json_data, params=params, timeout=15
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Shopify REST API request failed for {self.shop_domain}: {e}")
            raise

    def execute_graphql(
        self, query: str, variables: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Executes a request against the Shopify GraphQL API.
        """
        payload = {"query": query, "variables": variables or {}}
        try:
            response = self.session.post(self.graphql_url, json=payload, timeout=15)
            data = self._handle_response(response)
            if "errors" in data:
                logger.error(
                    f"GraphQL query for {self.shop_domain} returned errors: {data['errors']}"
                )
            return data
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Shopify GraphQL API request failed for {self.shop_domain}: {e}"
            )
            raise

    # --- Refactored Billing and Usage Charge Methods ---

    def create_recurring_application_charge(
        self,
        name: str,
        price: float,
        return_url: str,
        test: bool = True,
        trial_days: int = 30,
        capped_amount: float = 100.0,
        terms: str = "Usage-based charges",
    ) -> Dict[str, Any]:
        payload = {
            "recurring_application_charge": {
                "name": name,
                "price": price,
                "return_url": return_url,
                "test": test,
                "trial_days": trial_days,
                "capped_amount": capped_amount,
                "terms": terms,
            }
        }
        return self.execute_rest(
            "POST", "recurring_application_charges", json_data=payload
        )

    def activate_recurring_application_charge(self, charge_id: int) -> Dict[str, Any]:
        return self.execute_rest(
            "POST", f"recurring_application_charges/{charge_id}/activate"
        )

    def create_usage_charge(
        self,
        recurring_charge_id: int,
        description: str,
        price: float,
        quantity: int = 1,
    ) -> Dict[str, Any]:
        payload = {
            "usage_charge": {
                "description": description,
                "price": price,
                "quantity": quantity,
            }
        }
        return self.execute_rest(
            "POST",
            f"recurring_application_charges/{recurring_charge_id}/usage_charges",
            json_data=payload,
        )

    def get_recurring_application_charge(self, charge_id: int) -> Dict[str, Any]:
        return self.execute_rest("GET", f"recurring_application_charges/{charge_id}")

    def cancel_recurring_application_charge(self, charge_id: int) -> Dict[str, Any]:
        return self.execute_rest("DELETE", f"recurring_application_charges/{charge_id}")


# --- Dependency Injection Provider ---


def get_shopify_client(shop_domain: str, access_token: str) -> ShopifyClient:
    """
    Factory/provider function to instantiate and return a ShopifyClient.
    This can be used with a dependency injection system.
    """
    return ShopifyClient(shop_domain=shop_domain, access_token=access_token)
