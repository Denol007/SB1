"""Database session management for async SQLAlchemy.

This module provides:
- Async session factory configuration
- Connection pooling setup
- FastAPI dependency for database sessions
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.infrastructure.database.base import get_engine


def get_async_session_factory(**engine_kwargs: Any) -> async_sessionmaker[AsyncSession]:
    """Create and configure async session factory.

    Creates a session factory with optimized settings for async operations.
    Connection pooling is configured via the engine.

    Args:
        **engine_kwargs: Additional keyword arguments for engine creation.

    Returns:
        Configured async sessionmaker instance.

    Example:
        >>> # Get session factory
        >>> SessionFactory = get_async_session_factory()
        >>>
        >>> # Create a session
        >>> async with SessionFactory() as session:
        ...     result = await session.execute(select(User))
        ...     users = result.scalars().all()
    """
    # Create async engine with connection pooling
    engine = get_engine(
        database_url=settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DATABASE_ECHO,
        **engine_kwargs,
    )

    # Create session factory
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
        autocommit=False,  # Explicit transaction control
        autoflush=False,  # Manual flush control for better performance
    )


# Global session factory instance
SessionFactory = get_async_session_factory()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides database sessions.

    Yields an async database session and ensures it's properly closed
    after the request completes (even if an exception occurs).

    This dependency should be used in FastAPI path operations to get
    a database session for the request lifecycle.

    Yields:
        AsyncSession: Database session for the request.

    Example:
        >>> from fastapi import Depends
        >>> from app.infrastructure.database.session import get_db
        >>>
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(
        ...     user_id: str,
        ...     db: AsyncSession = Depends(get_db)
        ... ):
        ...     result = await db.execute(
        ...         select(User).where(User.id == user_id)
        ...     )
        ...     return result.scalar_one_or_none()
    """
    async with SessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
