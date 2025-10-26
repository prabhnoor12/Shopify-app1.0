"""
Request validation middleware to ensure the authenticity of incoming requests,
especially for Shopify webhooks.
"""

import base64
import hashlib
import hmac
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from my_app.exceptions import InvalidHmacError

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate incoming requests, with a focus on Shopify webhooks.
    """

    def __init__(self, app: ASGIApp, shopify_secret: str):
        super().__init__(app)
        self.shopify_secret = shopify_secret

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Validates the HMAC signature for Shopify webhook requests.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint in the chain.

        Returns:
            The response from the next middleware or endpoint.

        Raises:
            InvalidHmacError: If the HMAC validation fails.
        """
        if "X-Shopify-Hmac-Sha256" in request.headers:
            hmac_header = request.headers["X-Shopify-Hmac-Sha256"]
            request_body = await request.body()

            try:
                self.verify_hmac(request_body, hmac_header)
            except InvalidHmacError as e:
                logger.error("HMAC validation failed: %s", e)
                return Response(content="HMAC validation failed", status_code=401)

        response = await call_next(request)
        return response

    def verify_hmac(self, body: bytes, hmac_header: str) -> None:
        """
        Verifies the HMAC signature of the request body.

        Args:
            body: The request body.
            hmac_header: The value of the X-Shopify-Hmac-Sha256 header.

        Raises:
            InvalidHmacError: If the HMAC is invalid.
        """
        if not self.shopify_secret:
            raise InvalidHmacError("Shopify secret is not configured.")

        computed_hmac = base64.b64encode(
            hmac.new(self.shopify_secret.encode("utf-8"), body, hashlib.sha256).digest()
        )
        if not hmac.compare_digest(computed_hmac, hmac_header.encode("utf-8")):
            raise InvalidHmacError("HMAC signature does not match.")
