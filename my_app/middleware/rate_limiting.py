import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from ..dependencies.redis import get_redis_client
import redis.asyncio as redis


class AdvancedRateLimiter:
    def __init__(self, redis_client: redis.Redis, limit: int, period: int):
        self.redis = redis_client
        self.limit = limit
        self.period = period

    async def is_rate_limited(self, key: str) -> bool:
        """
        Checks if a given key is rate-limited using the sliding window log algorithm.
        """
        now = time.time()
        redis_key = f"rate_limit:{key}"

        async with self.redis.pipeline() as pipe:
            # Remove timestamps older than the window
            pipe.zremrangebyscore(redis_key, 0, now - self.period)
            # Add the current request timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Count the number of requests in the window
            pipe.zcard(redis_key)
            # Set an expiration for the key to auto-clean
            pipe.expire(redis_key, self.period)

            results = await pipe.execute()
            count = results[2]

        return count > self.limit


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 100, period: int = 60):
        super().__init__(app)
        self.redis_client = get_redis_client()
        self.limiter = AdvancedRateLimiter(self.redis_client, limit, period)

    async def dispatch(self, request: Request, call_next):
        # Use the client's IP address as the key for rate limiting.
        # For authenticated requests, you might want to use the user ID.
        client_key = request.client.host

        # Allow OPTIONS requests to pass through without rate limiting for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        if await self.limiter.is_rate_limited(client_key):
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )

        response = await call_next(request)
        return response
