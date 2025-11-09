"""Unit tests for cache service.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

import json
from unittest.mock import AsyncMock

import pytest

from app.infrastructure.cache.cache_service import CacheService


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client for testing."""
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def cache_service(mock_redis_client):
    """Create CacheService instance with mock Redis client."""
    return CacheService(mock_redis_client)


class TestCacheServiceGet:
    """Test cases for CacheService.get() method."""

    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self, cache_service, mock_redis_client):
        """Test that get returns the cached value."""
        mock_redis_client.get.return_value = "cached_value"

        result = await cache_service.get("test_key")

        assert result == "cached_value"
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self, cache_service, mock_redis_client):
        """Test that get returns None when key doesn't exist."""
        mock_redis_client.get.return_value = None

        result = await cache_service.get("missing_key")

        assert result is None
        mock_redis_client.get.assert_called_once_with("missing_key")

    @pytest.mark.asyncio
    async def test_get_deserializes_json_value(self, cache_service, mock_redis_client):
        """Test that get deserializes JSON values."""
        test_data = {"user_id": 123, "name": "Test User"}
        mock_redis_client.get.return_value = json.dumps(test_data)

        result = await cache_service.get("user:123", deserialize=True)

        assert result == test_data
        mock_redis_client.get.assert_called_once_with("user:123")

    @pytest.mark.asyncio
    async def test_get_handles_invalid_json(self, cache_service, mock_redis_client):
        """Test that get handles invalid JSON gracefully."""
        mock_redis_client.get.return_value = "invalid json {"

        result = await cache_service.get("test_key", deserialize=True)

        # Should return the raw string if JSON parsing fails
        assert result == "invalid json {"


class TestCacheServiceSet:
    """Test cases for CacheService.set() method."""

    @pytest.mark.asyncio
    async def test_set_stores_value(self, cache_service, mock_redis_client):
        """Test that set stores value in cache."""
        mock_redis_client.set.return_value = True

        result = await cache_service.set("test_key", "test_value")

        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test_value", None)

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_service, mock_redis_client):
        """Test that set accepts TTL parameter."""
        mock_redis_client.set.return_value = True

        await cache_service.set("test_key", "test_value", ttl=3600)

        mock_redis_client.set.assert_called_once_with("test_key", "test_value", 3600)

    @pytest.mark.asyncio
    async def test_set_serializes_dict_to_json(self, cache_service, mock_redis_client):
        """Test that set serializes dict values to JSON."""
        test_data = {"user_id": 123, "name": "Test User"}
        mock_redis_client.set.return_value = True

        await cache_service.set("user:123", test_data)

        # Should serialize to JSON
        expected_json = json.dumps(test_data)
        mock_redis_client.set.assert_called_once_with("user:123", expected_json, None)

    @pytest.mark.asyncio
    async def test_set_serializes_list_to_json(self, cache_service, mock_redis_client):
        """Test that set serializes list values to JSON."""
        test_data = [1, 2, 3, 4, 5]
        mock_redis_client.set.return_value = True

        await cache_service.set("test_list", test_data)

        # Should serialize to JSON
        expected_json = json.dumps(test_data)
        mock_redis_client.set.assert_called_once_with("test_list", expected_json, None)

    @pytest.mark.asyncio
    async def test_set_converts_int_to_string(self, cache_service, mock_redis_client):
        """Test that set converts integer values to string."""
        mock_redis_client.set.return_value = True

        await cache_service.set("counter", 42)

        mock_redis_client.set.assert_called_once_with("counter", "42", None)


class TestCacheServiceDelete:
    """Test cases for CacheService.delete() method."""

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis_client):
        """Test that delete removes key from cache."""
        mock_redis_client.delete.return_value = 1

        result = await cache_service.delete("test_key")

        assert result == 1
        mock_redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_returns_zero_when_key_not_found(self, cache_service, mock_redis_client):
        """Test that delete returns 0 when key doesn't exist."""
        mock_redis_client.delete.return_value = 0

        result = await cache_service.delete("missing_key")

        assert result == 0
        mock_redis_client.delete.assert_called_once_with("missing_key")


class TestCacheServiceBuildKey:
    """Test cases for CacheService.build_key() method."""

    def test_build_key_creates_namespaced_key(self, cache_service):
        """Test that build_key creates properly formatted key."""
        key = cache_service.build_key("user", "123")

        assert key == "user:123"

    def test_build_key_with_integer_identifier(self, cache_service):
        """Test that build_key handles integer identifiers."""
        key = cache_service.build_key("community", 456)

        assert key == "community:456"

    def test_build_key_with_multiple_parts(self, cache_service):
        """Test that build_key handles multiple key parts."""
        key = cache_service.build_key("user", "123", "profile")

        assert key == "user:123:profile"

    def test_build_key_with_empty_namespace(self, cache_service):
        """Test that build_key handles empty namespace."""
        key = cache_service.build_key("", "123")

        assert key == ":123"


class TestCacheServiceExists:
    """Test cases for CacheService.exists() method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_key_exists(self, cache_service, mock_redis_client):
        """Test that exists returns True when key is in cache."""
        mock_redis_client.client = AsyncMock()
        mock_redis_client.client.exists = AsyncMock(return_value=1)

        result = await cache_service.exists("test_key")

        assert result is True
        mock_redis_client.client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_key_not_found(self, cache_service, mock_redis_client):
        """Test that exists returns False when key doesn't exist."""
        mock_redis_client.client = AsyncMock()
        mock_redis_client.client.exists = AsyncMock(return_value=0)

        result = await cache_service.exists("missing_key")

        assert result is False
        mock_redis_client.client.exists.assert_called_once_with("missing_key")


class TestCacheServiceExpire:
    """Test cases for CacheService.expire() method."""

    @pytest.mark.asyncio
    async def test_expire_sets_ttl_on_key(self, cache_service, mock_redis_client):
        """Test that expire sets TTL on existing key."""
        mock_redis_client.client = AsyncMock()
        mock_redis_client.client.expire = AsyncMock(return_value=True)

        result = await cache_service.expire("test_key", 3600)

        assert result is True
        mock_redis_client.client.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_expire_returns_false_when_key_not_found(self, cache_service, mock_redis_client):
        """Test that expire returns False when key doesn't exist."""
        mock_redis_client.client = AsyncMock()
        mock_redis_client.client.expire = AsyncMock(return_value=False)

        result = await cache_service.expire("missing_key", 3600)

        assert result is False
        mock_redis_client.client.expire.assert_called_once_with("missing_key", 3600)
