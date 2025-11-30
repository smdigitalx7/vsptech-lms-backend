import redis.asyncio as redis
from typing import Optional, Any, Dict
import json
from app.core.logger import get_logger

logger = get_logger(__name__)

# Global cache client and pool
pool: Optional[redis.ConnectionPool] = None
client: Optional[redis.Redis] = None


class CacheManager:
    """Redis cache manager with proper error handling and connection management."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pool: Optional[redis.ConnectionPool] = None
        self._is_connected = False

    async def connect(self, redis_url: str) -> bool:
        """Connect to Redis server.

        Parameters
        ----------
        redis_url : str
            Redis connection URL.

        Returns
        -------
        bool
            True if connection successful, False otherwise.
        """
        try:
            self.pool = redis.ConnectionPool.from_url(redis_url)  # type: ignore[assignment]
            self.client = redis.Redis.from_pool(self.pool)

            # Test connection
            await self.client.ping()  # type: ignore[misc]
            self._is_connected = True
            logger.info("Redis cache connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("Redis cache disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis cache: {e}")
        self._is_connected = False

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis cache.

        Parameters
        ----------
        key : str
            The cache key to retrieve.

        Returns
        -------
        str | None
            The cached value if found, None otherwise.
        """
        if not self._is_connected or not self.client:
            return None

        try:
            value = await self.client.get(key)
            return value.decode() if value else None
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis cache.

        Parameters
        ----------
        key : str
            The cache key.
        value : str
            The value to cache.
        expire : int | None
            Expiration time in seconds (optional).

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        if not self._is_connected or not self.client:
            return False

        try:
            result = await self.client.set(key, value, ex=expire)
            logger.debug(f"Cache set for key '{key}'", success=bool(result))
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis cache.

        Parameters
        ----------
        key : str
            The cache key to delete.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        if not self._is_connected or not self.client:
            return False

        try:
            result = await self.client.delete(key)
            logger.debug(f"Cache delete for key '{key}'", success=bool(result))
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache.

        Parameters
        ----------
        key : str
            The cache key to check.

        Returns
        -------
        bool
            True if key exists, False otherwise.
        """
        if not self._is_connected or not self.client:
            return False

        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis cache.

        Parameters
        ----------
        key : str
            The cache key to retrieve.

        Returns
        -------
        dict | None
            The cached JSON value if found, None otherwise.
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key '{key}': {e}")
        return None

    async def set_json(self, key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set a JSON value in Redis cache.

        Parameters
        ----------
        key : str
            The cache key.
        value : dict
            The JSON value to cache.
        expire : int | None
            Expiration time in seconds (optional).

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key '{key}': {e}")
            return False

    async def health_check(self) -> bool:
        """Check Redis connection health.

        Returns
        -------
        bool
            True if Redis is healthy, False otherwise.
        """
        if not self._is_connected or not self.client:
            return False

        try:
            await self.client.ping()  # type: ignore[misc]
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()

