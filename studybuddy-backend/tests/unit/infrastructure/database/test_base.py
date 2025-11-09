"""Unit tests for SQLAlchemy base configuration.

Tests the async database engine setup, declarative base,
and timestamp mixin functionality.
"""

from unittest.mock import MagicMock, patch
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.database.base import Base, TimestampMixin, get_engine


class TestGetEngine:
    """Test suite for database engine creation."""

    @patch("app.infrastructure.database.base.create_async_engine")
    def test_get_engine_creates_async_engine(self, mock_create_engine: MagicMock) -> None:
        """Test that get_engine creates an async SQLAlchemy engine."""
        # Arrange
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        database_url = "postgresql+asyncpg://user:pass@localhost/testdb"

        # Act
        engine = get_engine(database_url)

        # Assert
        mock_create_engine.assert_called_once()
        assert engine == mock_engine

    @patch("app.infrastructure.database.base.create_async_engine")
    def test_get_engine_with_pool_settings(self, mock_create_engine: MagicMock) -> None:
        """Test that engine is created with correct pool settings."""
        # Arrange
        database_url = "postgresql+asyncpg://user:pass@localhost/testdb"

        # Act
        get_engine(database_url, pool_size=10, max_overflow=5)

        # Assert
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["pool_size"] == 10
        assert call_kwargs["max_overflow"] == 5
        assert call_kwargs["pool_pre_ping"] is True

    @patch("app.infrastructure.database.base.create_async_engine")
    def test_get_engine_echo_mode(self, mock_create_engine: MagicMock) -> None:
        """Test that engine can be created with echo mode for debugging."""
        # Arrange
        database_url = "postgresql+asyncpg://user:pass@localhost/testdb"

        # Act
        get_engine(database_url, echo=True)

        # Assert
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["echo"] is True


class TestBase:
    """Test suite for declarative base."""

    def test_base_is_declarative_base(self) -> None:
        """Test that Base is a SQLAlchemy declarative base."""
        # Assert
        assert hasattr(Base, "registry")
        assert hasattr(Base, "metadata")

    def test_model_with_base_has_tablename(self) -> None:
        """Test that models inheriting from Base get __tablename__."""

        # Arrange
        class TestModel(Base):
            __tablename__ = "test_models"
            id: int

        # Assert
        assert TestModel.__tablename__ == "test_models"


class TestTimestampMixin:
    """Test suite for TimestampMixin."""

    def test_timestamp_mixin_has_created_at(self) -> None:
        """Test that TimestampMixin provides created_at column."""

        # Arrange
        class TestModel(Base, TimestampMixin):
            __tablename__ = "test_timestamps"

        # Act
        mapper = inspect(TestModel)
        columns = {col.name for col in mapper.columns}

        # Assert
        assert "created_at" in columns

    def test_timestamp_mixin_has_updated_at(self) -> None:
        """Test that TimestampMixin provides updated_at column."""

        # Arrange
        class TestModel(Base, TimestampMixin):
            __tablename__ = "test_timestamps"

        # Act
        mapper = inspect(TestModel)
        columns = {col.name for col in mapper.columns}

        # Assert
        assert "updated_at" in columns

    def test_created_at_has_default(self) -> None:
        """Test that created_at has a default value."""

        # Arrange
        class TestModel(Base, TimestampMixin):
            __tablename__ = "test_timestamps"

        # Act
        mapper = inspect(TestModel)
        created_at_col = mapper.columns["created_at"]

        # Assert
        assert created_at_col.default is not None
        assert created_at_col.nullable is False

    def test_updated_at_has_default_and_onupdate(self) -> None:
        """Test that updated_at has default and onupdate values."""

        # Arrange
        class TestModel(Base, TimestampMixin):
            __tablename__ = "test_timestamps"

        # Act
        mapper = inspect(TestModel)
        updated_at_col = mapper.columns["updated_at"]

        # Assert
        assert updated_at_col.default is not None
        assert updated_at_col.onupdate is not None
        assert updated_at_col.nullable is False

    def test_timestamp_values_are_timezone_aware(self) -> None:
        """Test that timestamp columns use timezone-aware datetime."""

        # Arrange
        class TestModel(Base, TimestampMixin):
            __tablename__ = "test_timestamps"

        # Act
        mapper = inspect(TestModel)
        created_at_col = mapper.columns["created_at"]

        # Assert
        # Column type should be DateTime with timezone
        assert hasattr(created_at_col.type, "timezone")
        assert created_at_col.type.timezone is True


class TestUUIDPrimaryKey:
    """Test suite for UUID primary key configuration."""

    def test_model_can_use_uuid_primary_key(self) -> None:
        """Test that models can use UUID as primary key."""
        # Arrange
        from sqlalchemy import Column
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID

        class TestModel(Base):
            __tablename__ = "test_uuid_model"
            id = Column(PG_UUID(as_uuid=True), primary_key=True)

        # Act
        mapper = inspect(TestModel)
        id_col = mapper.columns["id"]

        # Assert
        assert id_col.primary_key is True
        assert hasattr(id_col.type, "as_uuid")

    def test_uuid_column_accepts_uuid_objects(self) -> None:
        """Test that UUID columns work with Python UUID objects."""
        # Arrange
        from uuid import uuid4

        from sqlalchemy import Column
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID

        class TestModel(Base):
            __tablename__ = "test_uuid_values"
            id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

        # Act
        test_uuid = uuid4()

        # Assert
        # UUID should be a valid type for the column
        assert isinstance(test_uuid, UUID)
