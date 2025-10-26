import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from my_app.exceptions import (
    ShopifyAuthException,
    PermissionDeniedException,
    ValidationException,
    InvalidHmacError,
)


def add_exception_handlers(app: FastAPI):
    """Add custom exception handlers to the FastAPI app."""

    @app.exception_handler(InvalidHmacError)
    async def invalid_hmac_exception_handler(request: Request, exc: InvalidHmacError):
        """Handle invalid HMAC errors."""
        logging.warning(
            f"Invalid HMAC for request {request.method} {request.url.path}: {exc.message}"
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message or "Invalid HMAC."},
        )

    @app.exception_handler(ShopifyAuthException)
    async def shopify_auth_exception_handler(
        request: Request, exc: ShopifyAuthException
    ):
        """Handle Shopify authentication errors."""
        logging.warning(
            f"Shopify authentication failed for request {request.method} {request.url.path}: {exc.message}"
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message or "Shopify authentication failed."},
        )

    @app.exception_handler(PermissionDeniedException)
    async def permission_denied_exception_handler(
        request: Request, exc: PermissionDeniedException
    ):
        """Handle permission denied errors."""
        logging.warning(
            f"Permission denied for request {request.method} {request.url.path}: {exc.message}"
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": exc.message
                or "You do not have permission to perform this action."
            },
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle custom validation errors."""
        logging.warning(
            f"Validation error for request {request.method} {request.url.path}: {exc.message}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.to_dict()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle FastAPI's built-in HTTP exceptions."""
        logging.info(
            f"HTTP exception for request {request.method} {request.url.path}: {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors."""
        logging.warning(
            f"Request validation error for request {request.method} {request.url.path}: {exc.errors()}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all uncaught exceptions."""
        logging.critical(
            f"An unexpected error occurred for request {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        )
