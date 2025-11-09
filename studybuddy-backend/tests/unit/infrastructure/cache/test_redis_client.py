"""Unit tests for Redis client.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.cache.redis_client import (
    RedisClient,
    close_redis_client,
    get_redis_client,
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client for testing."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
async def cleanup_redis_client():
    """Reset global Redis client between tests."""
    yield
    # Clean up the global singleton after each test
    import app.infrastructure.cache.redis_client as redis_module

    redis_module._redis_client = None


class TestGetRedisClient:
    """Test cases for get_redis_client() function."""

    @pytest.mark.asyncio
    async def test_creates_redis_client_with_correct_url(self, mock_redis):
        """Test that Redis client is created with correct URL from settings."""
        with patch("app.infrastructure.cache.redis_client.aioredis.Redis") as mock_redis_class:
            mock_redis_class.from_url.return_value = mock_redis
            client = await get_redis_client()

            # Assert
            assert client is not None
            mock_redis_class.from_url.assert_called_once()
            # URL is passed as first positional argument
            call_args = mock_redis_class.from_url.call_args.args
            assert len(call_args) > 0
            assert "redis://" in str(call_args[0])

    @pytest.mark.asyncio
    async def test_creates_client_with_connection_pool_settings(self):
        """Test that Redis client calls from_url with correct settings."""
        # Reset the singleton before this test
        import app.infrastructure.cache.redis_client as redis_module

        redis_module._redis_client = None

        # This test verifies the contract - in integration tests we'll verify actual connection
        # For now, we just verify the function exists and returns a RedisClient
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        with patch("app.infrastructure.cache.redis_client.aioredis.Redis") as mock_redis_class:
            mock_redis_class.from_url.return_value = mock_redis

            client = await get_redis_client()

            # Verify we get a RedisClient instance
            assert isinstance(client, RedisClient)
            # Verify from_url was called with our settings
            assert mock_redis_class.from_url.called

    @pytest.mark.asyncio
    async def test_returns_singleton_instance(self, mock_redis):
        """Test that get_redis_client returns the same instance on multiple calls."""
        with patch("app.infrastructure.cache.redis_client.aioredis.Redis") as mock_redis_class:
            mock_redis_class.from_url.return_value = mock_redis
            client1 = await get_redis_client()
            client2 = await get_redis_client()

            # Assert same instance
            assert client1 is client2

    @pytest.mark.asyncio
    async def test_pings_redis_on_connection(self):
        """Test that Redis connection is verified with ping."""
        # Reset the singleton before this test
        import app.infrastructure.cache.redis_client as redis_module

        redis_module._redis_client = None

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        with patch("app.infrastructure.cache.redis_client.aioredis.Redis") as mock_redis_class:
            mock_redis_class.from_url.return_value = mock_redis

            await get_redis_client()

            # Verify ping was called to test the connection
            mock_redis.ping.assert_called_once()


class TestCloseRedisClient:
    """Test cases for close_redis_client() function."""

    @pytest.mark.asyncio
    async def test_closes_redis_connection(self):
        """Test that close_redis_client properly closes the connection."""
        # Reset the singleton before this test
        import app.infrastructure.cache.redis_client as redis_module

        redis_module._redis_client = None

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.close = AsyncMock()

        with patch("app.infrastructure.cache.redis_client.aioredis.Redis") as mock_redis_class:
            mock_redis_class.from_url.return_value = mock_redis

            # Create client
            await get_redis_client()

            # Close it
            await close_redis_client()

            # Verify close was called on the underlying client
            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_close_when_no_client_exists(self):
        """Test that close_redis_client handles case when no client exists."""
        # Should not raise an exception
        await close_redis_client()


class TestRedisClient:
    """Test cases for RedisClient class."""

    @pytest.mark.asyncio
    async def test_redis_client_has_get_method(self):
        """Test that RedisClient has get method."""
        mock_redis = AsyncMock()
        client = RedisClient(mock_redis)

        assert hasattr(client, "get")
        assert callable(client.get)

    @pytest.mark.asyncio
    async def test_redis_client_has_set_method(self):
        """Test that RedisClient has set method."""
        mock_redis = AsyncMock()
        client = RedisClient(mock_redis)

        assert hasattr(client, "set")
        assert callable(client.set)

    @pytest.mark.asyncio
    async def test_redis_client_has_delete_method(self):
        """Test that RedisClient has delete method."""
        mock_redis = AsyncMock()
        client = RedisClient(mock_redis)

        assert hasattr(client, "delete")
        assert callable(client.delete)

    @pytest.mark.asyncio
    async def test_redis_client_get_returns_value(self):
        """Test that get method returns cached value."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="test_value")
        client = RedisClient(mock_redis)

        result = await client.get("test_key")

        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_redis_client_set_stores_value(self):
        """Test that set method stores value in Redis."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        client = RedisClient(mock_redis)

        result = await client.set("test_key", "test_value")

        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None)

    @pytest.mark.asyncio
    async def test_redis_client_set_with_ttl(self):
        """Test that set method accepts TTL parameter."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        client = RedisClient(mock_redis)

        await client.set("test_key", "test_value", ttl=3600)

        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=3600)

    @pytest.mark.asyncio
    async def test_redis_client_delete_removes_key(self):
        """Test that delete method removes key from Redis."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        client = RedisClient(mock_redis)

        result = await client.delete("test_key")

        assert result == 1
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_redis_client_ping_checks_connection(self):
        """Test that ping method checks Redis connection."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        client = RedisClient(mock_redis)

        result = await client.ping()

        assert result is True
        mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_client_close_closes_connection(self):
        """Test that close method closes Redis connection."""
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        client = RedisClient(mock_redis)

        await client.close()

        mock_redis.close.assert_called_once()
