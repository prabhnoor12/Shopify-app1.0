"""
Advanced logging middleware for FastAPI.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging
import time

logger = logging.getLogger("my_app.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        query_string = request.url.query
        log_message = (
            f"{request.method} {request.url.path}"
            f"?{query_string if query_string else ''} "
            f"- {response.status_code} - {process_time:.2f}ms "
            f"- IP: {client_ip} - UA: {user_agent}"
        )
        logger.info(log_message)
        return response


def add_logging_middleware(app):
    """
    Adds the logging middleware to the FastAPI app.
    """
    app.add_middleware(LoggingMiddleware)
