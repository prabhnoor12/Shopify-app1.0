
import os
import time
import threading
import asyncio
import redis.asyncio as redis

# Cache a single Redis client and refresh it periodically to avoid stale
# connections (useful for long-running processes where connections can die).
# By default refresh every 3 hours; override with REDIS_CLIENT_REFRESH_SECONDS.
_cached_client: redis.Redis | None = None
_last_created: float = 0.0
_lock = threading.Lock()
_REFRESH_SECONDS = int(os.environ.get("REDIS_CLIENT_REFRESH_SECONDS", str(3 * 60 * 60)))


def _create_client():
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable is not set.")
    return redis.from_url(redis_url, decode_responses=True)


def get_redis_client():
    """Return a cached async Redis client, recreating it if older than
    REDIS_CLIENT_REFRESH_SECONDS. The returned client is an instance from
    `redis.asyncio.from_url` and can be used in async code.

    The function is thread-safe and will attempt to close the previous
    client when refreshing. If an event loop is running it will schedule
    waiting for the client's shutdown via `wait_closed()`.
    """
    global _cached_client, _last_created
    now = time.time()
    with _lock:
        if _cached_client is None or (now - _last_created) > _REFRESH_SECONDS:
            # close previous client if present
            if _cached_client is not None:
                try:
                    _cached_client.close()
                except Exception:
                    # best-effort close; ignore errors
                    pass
                # if loop is running, schedule wait_closed()
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        try:
                            asyncio.create_task(_cached_client.wait_closed())
                        except Exception:
                            # ignore scheduling errors
                            pass
                except Exception:
                    # if there is no running loop or other issue, ignore
                    pass

            _cached_client = _create_client()
            _last_created = now

        return _cached_client

