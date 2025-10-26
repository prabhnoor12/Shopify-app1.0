
import os
import redis.asyncio as redis

def get_redis_client():
    """
    Returns an async Redis client using REDIS_URL from environment variables.
    """
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable is not set.")
    return redis.from_url(redis_url, decode_responses=True)

