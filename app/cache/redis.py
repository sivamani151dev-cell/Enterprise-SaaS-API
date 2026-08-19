import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

redis_client: aioredis.Redis = None

async def connect_redis() -> None:
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding = "utf-8",
            decode_responses = True,
            max_connections = 20
        )
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error("Redis connection failed", 
                     extra={
                         "error": str(e)
                     })
        raise

async def disconnect_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis disconnected")

def get_redis() -> aioredis.Redis:
    return redis_client

async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    try:
        await redis_client.setex(key, ttl, value)
        logger.debug("Cache set",
                     extra={"key": key, "ttl": ttl})
    except Exception as e:
        logger.warning("Cache set failed",
                       extra= {"key": key,
                               "error": str(e)})

async def cache_get(key: str) -> str | None:
    try:
        value = await redis_client.get(key)
        if value:
            logger.debug("Cache hit", extra={"key": key})
        else:
            logger.debug("Cache miss", extra={"key": key})
        return value
    except Exception as e:
        logger.warning("Cache get failed", extra={"key": key, "error": str(e)})
        return None


async def cache_delete(key: str) -> None:
    """
    Delete a specific key from Redis.
    Call this when data is updated — invalidate the cache.
    
    Usage:
    await cache_delete("org:abc-slug")
    """
    try:
        await redis_client.delete(key)
        logger.debug("Cache deleted", extra={"key": key})
    except Exception as e:
        logger.warning("Cache delete failed", extra={"key": key, "error": str(e)})


async def cache_delete_pattern(pattern: str) -> None:
    """
    Delete all keys matching a pattern.
    Use when one update invalidates multiple cache entries.
    
    Usage:
    await cache_delete_pattern("org:abc-slug:*")
    This deletes: org:abc-slug:members, org:abc-slug:projects etc
    """
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug(
                "Cache pattern deleted",
                extra={"pattern": pattern, "keys_deleted": len(keys)}
            )
    except Exception as e:
        logger.warning(
            "Cache pattern delete failed",
            extra={"pattern": pattern, "error": str(e)}
        )


class CacheKeys:
    """
    All cache keys defined in one place.
    Never hardcode cache key strings in routers.

    Usage:
    key = CacheKeys.org(slug)          → "org:my-company"
    key = CacheKeys.org_members(slug)  → "org:my-company:members"
    key = CacheKeys.user(user_id)      → "user:uuid-here"
    """

    @staticmethod
    def org(slug: str) -> str:
        return f"org:{slug}"

    @staticmethod
    def org_members(slug: str) -> str:
        return f"org:{slug}:members"

    @staticmethod
    def org_projects(slug: str) -> str:
        return f"org:{slug}:projects"

    @staticmethod
    def project(project_id: str) -> str:
        return f"project:{project_id}"

    @staticmethod
    def project_tasks(project_id: str) -> str:
        return f"project:{project_id}:tasks"

    @staticmethod
    def user(user_id: str) -> str:
        return f"user:{user_id}"

    @staticmethod
    def api_keys(org_id: str) -> str:
        return f"org:{org_id}:api_keys"