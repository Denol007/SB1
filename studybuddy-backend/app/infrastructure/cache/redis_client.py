"""Redis client initialization and configuration.

This module provides async Redis client with connection pooling.
Follows singleton pattern to reuse connections across the application.
"""

from typing import Optional

from redis import asyncio as aioredis

from app.core.config import settings

# Global Redis client instance (singleton)
_redis_client: Optional["RedisClient"] = None


class RedisClient:
    """Wrapper around Redis async client with convenience methods.

    Attributes:
        client: The underlying Redis async client instance.
    """

    def __init__(self, client: aioredis.Redis):
        """Initialize Redis client wrapper.

        Args:
            client: Redis async client instance.
        """
        self.client = client

    async def get(self, key: str) -> str | None:
        """Get value from Redis.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found.
        """
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool | None:
        """Set value in Redis with optional TTL.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time to live in seconds (optional).

        Returns:
            True if successful, None otherwise.
        """
        return await self.client.set(key, value, ex=ttl)

    async def setex(self, key: str, seconds: int, value: str | int) -> bool | None:
        """Set value with expiration time.

        Args:
            key: The cache key.
            seconds: Expiration time in seconds.
            value: The value to cache.

        Returns:
            True if successful, None otherwise.
        """
        return await self.client.setex(key, seconds, str(value))

    async def incr(self, key: str) -> int:
        """Increment value by 1.

        Args:
            key: The cache key.

        Returns:
            The new value after incrementing.
        """
        return await self.client.incr(key)

    async def ttl(self, key: str) -> int:
        """Get time to live for key.

        Args:
            key: The cache key.

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist.
        """
        return await self.client.ttl(key)

    async def delete(self, key: str) -> int:
        """Delete key from Redis.

        Args:
            key: The cache key to delete.

        Returns:
            Number of keys deleted (0 or 1).
        """
        return await self.client.delete(key)

    async def ping(self) -> bool:
        """Ping Redis to check connection.

        Returns:
            True if connection is alive, False otherwise.
        """
        return await self.client.ping()

    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()


async def get_redis_client() -> RedisClient:
    """Get or create Redis client instance (singleton).

    Returns:
        RedisClient: Configured Redis client instance.

    Raises:
        redis.ConnectionError: If unable to connect to Redis.
    """
    global _redis_client

    if _redis_client is None:
        # Create Redis client with connection pool
        redis = aioredis.Redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            encoding="utf-8",
        )

        # Verify connection
        await redis.ping()

        _redis_client = RedisClient(redis)

    return _redis_client


async def close_redis_client() -> None:
    """Close the global Redis client connection.

    This should be called on application shutdown.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
