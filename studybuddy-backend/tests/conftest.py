"""Pytest configuration and fixtures for StudyBuddy tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.database.base import Base


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure async backend for pytest-asyncio."""
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a test database session for integration tests.

    This fixture creates a fresh database session for each test function,
    automatically creating and dropping all tables. Tests are isolated
    and run against a real PostgreSQL database.

    Yields:
        AsyncSession: Database session for testing.
    """
    # Use test database URL - assumes Docker container is running
    TEST_DATABASE_URL = (
        "postgresql+asyncpg://studybuddy:studybuddy_dev@localhost:5432/studybuddy_test"
    )

    # Create async engine with NullPool to avoid connection issues
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create and yield session
    async with async_session_factory() as session:
        yield session
        await session.rollback()

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await engine.dispose()
