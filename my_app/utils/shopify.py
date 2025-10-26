import os
import hmac
import hashlib
import base64
import re
import logging
from fastapi import Request
from urllib.parse import urlencode
from typing import Optional

from my_app.core.config import settings
from my_app.exceptions import InvalidHmacError, ShopifyDomainError

logger = logging.getLogger(__name__)

SHOPIFY_DOMAIN_REGEX = re.compile(
    r"^(?=.{1,253}\.myshopify\.com$)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.myshopify\.com$"
)



def _verify_hmac(
    secret: str, message: bytes, hmac_to_verify: str, is_base64: bool = False
) -> None:
    """Helper to verify HMAC signatures."""
    if not secret:
        logger.error("Cannot verify HMAC: secret is not set.")
        raise InvalidHmacError("Server configuration error.")

    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    if is_base64:
        try:
            hmac_to_verify_bytes = base64.b64decode(hmac_to_verify)
        except (ValueError, TypeError):
            raise InvalidHmacError("Invalid HMAC format.")
    else:
        hmac_to_verify_bytes = hmac_to_verify.encode("utf-8")

    if not hmac.compare_digest(digest, hmac_to_verify_bytes):
        raise InvalidHmacError("HMAC verification failed.")


async def verify_shopify_hmac(request: Request) -> None:
    """
    Verify the HMAC signature from a Shopify request's query parameters.
    Raises InvalidHmacError on failure.
    """
    query_params = dict(request.query_params)
    hmac_to_verify = query_params.pop("hmac", None)

    if not hmac_to_verify:
        raise InvalidHmacError("HMAC parameter missing.")

    message = urlencode(sorted(query_params.items())).encode("utf-8")
    _verify_hmac(settings.shopify.api_secret, message, hmac_to_verify)


async def verify_shopify_webhook(request: Request) -> None:
    """
    Verifies the HMAC signature of a Shopify webhook request.
    Raises InvalidHmacError on failure.
    """
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header:
        raise InvalidHmacError("HMAC header missing.")

    request_body = await request.body()
    _verify_hmac(
        settings.shopify.webhook_secret, request_body, hmac_header, is_base64=True
    )


def format_shop_domain(shop_domain: str) -> str:
    """
    Formats and validates the shop domain.
    Raises ShopifyDomainError on failure.
    """
    if not isinstance(shop_domain, str) or not shop_domain.strip():
        raise ShopifyDomainError("Domain is empty or not a string.")
    shop_domain = shop_domain.strip().lower()
    if not shop_domain.endswith(".myshopify.com"):
        shop_domain = f"{shop_domain}.myshopify.com"

    if not is_valid_shop_domain(shop_domain):
        raise ShopifyDomainError(f"Invalid Shopify domain: {shop_domain}")
    return shop_domain


def is_valid_shop_domain(shop_domain: str) -> bool:
    """
    Validates if the provided shop domain is a valid Shopify domain.
    """
    if not isinstance(shop_domain, str):
        return False
    return bool(SHOPIFY_DOMAIN_REGEX.match(shop_domain))
