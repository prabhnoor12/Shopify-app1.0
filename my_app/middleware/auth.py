"""
Authentication middleware for FastAPI.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse
import re
import logging
import os
from ..utils.shopify import is_valid_shop_domain

logger = logging.getLogger(__name__)

# Define paths that should not be protected by authentication
PUBLIC_PATHS = [
    "/",
    "/shopify/install",
    "/shopify/callback",
    "/auth/install",
    "/auth/callback",
    "/docs",
    "/redoc",
    "/openapi.json",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow requests in development mode without authentication
        if os.getenv("APP_ENV") == "development":
            logger.info("Skipping authentication for local development.")
            return await call_next(request)

        # Bypass authentication for public paths and static files
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/static"):
            response = await call_next(request)
            return response

        token = request.headers.get("X-Shop-Token")
        shop_domain = request.headers.get("X-Shop-Domain")

        # Check for missing headers
        if not token:
            logger.warning("Missing authentication token from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token."},
            )
        if not shop_domain:
            logger.warning("Missing shop domain header from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing shop domain header."},
            )

        # Validate token format (e.g., must be a hex string of length 32 or JWT-like)
        if not (
            re.fullmatch(r"[a-fA-F0-9]{32}", token)
            or re.fullmatch(r"[\w-]+\.[\w-]+\.[\w-]+", token)
        ):
            logger.warning(
                "Invalid token format from %s: %s", request.client.host, token
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token format."},
            )

        # Validate shop domain format
        if not is_valid_shop_domain(shop_domain):
            logger.warning(
                "Invalid shop domain from %s: %s", request.client.host, shop_domain
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid shop domain format."},
            )

        # You can add more logic here (e.g., check user in DB, rate limiting, etc.)

        response = await call_next(request)
        return response
