import json
import functools
from app.cache.redis import cache_get, cache_set
from app.core.logging import get_logger

logger = get_logger(__name__)


def cache_response(key_prefix: str, ttl: int = 300):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from prefix + all arguments
            key_parts = [key_prefix] + [str(a) for a in args] + [str(v) for v in kwargs.values()]
            cache_key = ":".join(key_parts)

            # Check cache first
            cached = await cache_get(cache_key)
            if cached:
                return json.loads(cached)

            # Cache miss — call actual function
            result = await func(*args, **kwargs)

            # Store result in cache
            if result is not None:
                await cache_set(cache_key, json.dumps(result), ttl=ttl)

            return result
        return wrapper
    return decorator