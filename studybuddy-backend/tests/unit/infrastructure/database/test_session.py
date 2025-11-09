"""Unit tests for database session management.

Tests async session factory, connection pooling,
and FastAPI dependency integration.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import (
    get_async_session_factory,
    get_db,
)


class TestAsyncSessionFactory:
    """Test suite for async session factory creation."""

    @patch("app.infrastructure.database.session.async_sessionmaker")
    @patch("app.infrastructure.database.session.get_engine")
    def test_get_async_session_factory_creates_sessionmaker(
        self, mock_get_engine: MagicMock, mock_sessionmaker: MagicMock
    ) -> None:
        """Test that session factory is created with async engine."""
        # Arrange
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_factory = MagicMock()
        mock_sessionmaker.return_value = mock_factory

        # Act
        factory = get_async_session_factory()

        # Assert
        mock_get_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()
        assert factory == mock_factory

    @patch("app.infrastructure.database.session.async_sessionmaker")
    @patch("app.infrastructure.database.session.get_engine")
    def test_session_factory_configuration(
        self, mock_get_engine: MagicMock, mock_sessionmaker: MagicMock
    ) -> None:
        """Test that session factory is configured correctly."""
        # Arrange
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        # Act
        get_async_session_factory()

        # Assert
        call_kwargs = mock_sessionmaker.call_args[1]
        assert call_kwargs["class_"] == AsyncSession
        assert call_kwargs["expire_on_commit"] is False
        assert call_kwargs["autocommit"] is False
        assert call_kwargs["autoflush"] is False


class TestGetDBDependency:
    """Test suite for FastAPI database dependency."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self) -> None:
        """Test that get_db yields an async session."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.infrastructure.database.session.get_async_session_factory",
            return_value=mock_factory,
        ):
            # Act
            generator = get_db()
            session = await generator.__anext__()

            # Assert
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_db_closes_session_after_use(self) -> None:
        """Test that get_db properly closes session after use."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_factory.return_value = mock_context_manager

        with patch(
            "app.infrastructure.database.session.get_async_session_factory",
            return_value=mock_factory,
        ):
            # Act
            generator = get_db()
            _ = await generator.__anext__()

            try:
                await generator.__anext__()
            except StopAsyncIteration:
                pass

            # Assert
            mock_context_manager.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_closes_session_on_exception(self) -> None:
        """Test that get_db closes session even if exception occurs."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_factory.return_value = mock_context_manager

        with patch(
            "app.infrastructure.database.session.get_async_session_factory",
            return_value=mock_factory,
        ):
            # Act
            generator = get_db()
            _ = await generator.__anext__()

            try:
                await generator.athrow(Exception("Test error"))
            except Exception:
                pass

            # Assert
            mock_context_manager.__aexit__.assert_called_once()


class TestConnectionPooling:
    """Test suite for connection pool configuration."""

    @patch("app.infrastructure.database.session.get_engine")
    def test_default_pool_size(self, mock_get_engine: MagicMock) -> None:
        """Test that default pool size is set correctly."""
        # Arrange & Act
        get_async_session_factory()

        # Assert
        # Engine should be created with default pool settings
        call_kwargs = mock_get_engine.call_args[1]
        assert call_kwargs.get("pool_size") == 5

    @patch("app.infrastructure.database.session.get_engine")
    def test_max_overflow(self, mock_get_engine: MagicMock) -> None:
        """Test that max overflow is set correctly."""
        # Arrange & Act
        get_async_session_factory()

        # Assert
        call_kwargs = mock_get_engine.call_args[1]
        assert call_kwargs.get("max_overflow") == 20
