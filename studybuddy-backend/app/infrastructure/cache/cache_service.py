"""Cache service with high-level caching operations.

This module provides a CacheService class that wraps the Redis client
with convenient methods for caching operations including:
- Namespace-based key management
- JSON serialization/deserialization
- TTL (time-to-live) support
- Existence checking
"""

import json
from typing import Any

from app.infrastructure.cache.redis_client import RedisClient


class CacheService:
    """High-level cache service with namespace support.

    This service provides convenient methods for caching operations
    with automatic JSON serialization and namespace-based key management.

    Example:
        >>> cache = CacheService(redis_client)
        >>> key = cache.build_key("user", user_id)
        >>> await cache.set(key, user_data, ttl=3600)
        >>> data = await cache.get(key, deserialize=True)

    Attributes:
        redis_client: The underlying Redis client instance.
    """

    def __init__(self, redis_client: RedisClient):
        """Initialize cache service.

        Args:
            redis_client: Configured Redis client instance.
        """
        self.redis_client = redis_client

    def build_key(self, *parts: str | int) -> str:
        """Build a namespaced cache key from parts.

        Args:
            *parts: Key parts to join with ':'.

        Returns:
            Namespaced key string.

        Example:
            >>> cache.build_key("user", 123)
            'user:123'
            >>> cache.build_key("user", 123, "profile")
            'user:123:profile'
        """
        return ":".join(str(part) for part in parts)

    async def get(
        self,
        key: str,
        deserialize: bool = False,
    ) -> Any | None:
        """Get value from cache.

        Args:
            key: The cache key.
            deserialize: If True, deserialize JSON value to dict/list.

        Returns:
            The cached value or None if not found.
            If deserialize=True, returns deserialized dict/list or raw string on error.

        Example:
            >>> value = await cache.get("user:123")
            >>> user = await cache.get("user:123", deserialize=True)
        """
        value = await self.redis_client.get(key)

        if value is None:
            return None

        if deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return raw string if JSON parsing fails
                return value

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool | None:
        """Set value in cache with optional TTL.

        Automatically serializes dict and list values to JSON.
        Converts other types to string.

        Args:
            key: The cache key.
            value: The value to cache (dict, list, str, int, etc.).
            ttl: Time to live in seconds (optional).

        Returns:
            True if successful, None otherwise.

        Example:
            >>> await cache.set("counter", 42, ttl=60)
            >>> await cache.set("user:123", {"name": "Alice"}, ttl=3600)
        """
        # Serialize dicts and lists to JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        # Convert other types to string
        elif not isinstance(value, str):
            value = str(value)

        return await self.redis_client.set(key, value, ttl)

    async def delete(self, key: str) -> int:
        """Delete key from cache.

        Args:
            key: The cache key to delete.

        Returns:
            Number of keys deleted (0 or 1).

        Example:
            >>> deleted = await cache.delete("user:123")
            >>> assert deleted == 1
        """
        return await self.redis_client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists, False otherwise.

        Example:
            >>> if await cache.exists("user:123"):
            ...     user = await cache.get("user:123")
        """
        result = await self.redis_client.client.exists(key)
        return result > 0  # type: ignore[no-any-return]

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key.

        Args:
            key: The cache key.
            ttl: Time to live in seconds.

        Returns:
            True if TTL was set, False if key doesn't exist.

        Example:
            >>> success = await cache.expire("user:123", 3600)
        """
        return await self.redis_client.client.expire(key, ttl)  # type: ignore[no-any-return]
