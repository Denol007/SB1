"""SQLAlchemy base configuration for async database operations.

This module provides the foundational database setup including:
- Async SQLAlchemy engine creation
- Declarative base for all models
- TimestampMixin for automatic created_at/updated_at tracking
- UUID primary key support
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All database models should inherit from this class. It provides:
    - Automatic table name generation (class name to snake_case)
    - Common configuration for all models
    - Type annotation support

    Example:
        >>> from sqlalchemy import Column, String
        >>> from sqlalchemy.dialects.postgresql import UUID
        >>> from uuid import uuid4
        >>>
        >>> class User(Base):
        ...     __tablename__ = "users"
        ...     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
        ...     email = Column(String, nullable=False, unique=True)
    """

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns.

    Automatically tracks creation and update times for any model.
    All timestamps are timezone-aware (UTC).

    Attributes:
        created_at: Timestamp when the record was created (set once).
        updated_at: Timestamp when the record was last updated (auto-updated).

    Example:
        >>> class User(Base, TimestampMixin):
        ...     __tablename__ = "users"
        ...     id = Column(UUID(as_uuid=True), primary_key=True)
        >>>
        >>> # User model now has created_at and updated_at columns
        >>> # created_at is set on insert
        >>> # updated_at is updated on every UPDATE
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Timestamp when the record was created."""
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """Timestamp when the record was last updated."""
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            onupdate=lambda: datetime.now(UTC),
            nullable=False,
        )


def get_engine(
    database_url: str,
    pool_size: int = 5,
    max_overflow: int = 20,
    echo: bool = False,
    **kwargs: Any,
) -> AsyncEngine:
    """Create and configure async SQLAlchemy engine.

    Creates an async engine for PostgreSQL with connection pooling and
    health check configuration. Uses asyncpg driver for async operations.

    Args:
        database_url: PostgreSQL connection URL (must use postgresql+asyncpg://).
        pool_size: Number of connections to maintain in the pool (default: 5).
        max_overflow: Max connections beyond pool_size (default: 20).
        echo: If True, log all SQL statements (useful for debugging).
        **kwargs: Additional arguments passed to create_async_engine.

    Returns:
        Configured AsyncEngine instance.

    Example:
        >>> from app.core.config import settings
        >>>
        >>> # Create engine from settings
        >>> engine = get_engine(
        ...     database_url=settings.DATABASE_URL,
        ...     pool_size=10,
        ...     max_overflow=30,
        ...     echo=settings.DEBUG
        ... )
        >>>
        >>> # Use in session factory
        >>> from sqlalchemy.ext.asyncio import async_sessionmaker
        >>> SessionFactory = async_sessionmaker(engine)
    """
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,  # Verify connections before using
        echo=echo,
        **kwargs,
    )
