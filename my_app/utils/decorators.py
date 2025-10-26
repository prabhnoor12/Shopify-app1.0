import time
import logging
from functools import wraps
from typing import Any, Callable, TypeVar
from openai import APIError, RateLimitError
import httpx

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

def retry_sync(func: F) -> F:
    """
    A decorator to automatically retry a synchronous function on specific
    network-related errors (RateLimitError, APIError, httpx.RequestError).
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        max_retries = 3
        delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (RateLimitError, APIError, httpx.RequestError) as e:
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %d seconds...",
                    attempt + 1,
                    max_retries,
                    func.__name__,
                    e,
                    delay,
                )
                if attempt + 1 == max_retries:
                    logger.error("Function %s failed after %d retries.", func.__name__, max_retries)
                    raise  # Re-raise the exception after the final attempt
                time.sleep(delay)
                delay *= 2  # Exponential backoff
    return wrapper
