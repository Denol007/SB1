"""Cache infrastructure package.

This package provides Redis-based caching functionality:
- Redis client with connection pooling (redis_client.py)
- High-level cache service with namespace support (cache_service.py)
"""

from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.cache.redis_client import (
    RedisClient,
    close_redis_client,
    get_redis_client,
)

__all__ = [
    "CacheService",
    "RedisClient",
    "get_redis_client",
    "close_redis_client",
]
