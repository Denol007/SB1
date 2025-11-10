"""Pytest configuration and fixtures for StudyBuddy tests."""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.domain.enums.user_role import UserRole
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.university import University
from app.infrastructure.database.models.user import User
from app.main import app


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


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    """Create async HTTP client for testing API endpoints.

    Args:
        db_session: Database session fixture

    Yields:
        AsyncClient: HTTP client for making requests
    """
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database.

    Args:
        db_session: Database session fixture

    Returns:
        User: Test user instance
    """
    user = User(
        id=uuid4(),
        google_id="google-test-user-123",
        email="testuser@example.com",
        name="Test User",
        bio="This is a test user",
        avatar_url="https://example.com/avatar.jpg",
        role=UserRole.PROSPECTIVE_STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def another_user(db_session: AsyncSession) -> User:
    """Create another test user in the database.

    Args:
        db_session: Database session fixture

    Returns:
        User: Another test user instance
    """
    user = User(
        id=uuid4(),
        google_id="google-another-user-456",
        email="anotheruser@example.com",
        name="Another User",
        bio="This is another test user",
        avatar_url="https://example.com/avatar2.jpg",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_university(db_session: AsyncSession) -> University:
    """Create a test university in the database.

    Args:
        db_session: Database session fixture

    Returns:
        University: Test university instance
    """
    university = University(
        id=uuid4(),
        name="Test University",
        domain="test.edu",
        country="United States",
        logo_url="https://example.com/logo.png",
    )
    db_session.add(university)
    await db_session.commit()
    await db_session.refresh(university)
    return university
