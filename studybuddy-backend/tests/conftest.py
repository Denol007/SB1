"""Pytest configuration and fixtures for StudyBuddy tests."""

import asyncio
import os
from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Set event loop policy for consistent async behavior across tests
if os.name == "nt":  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:  # Unix/Linux/Mac
    try:
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass  # Use default policy if uvloop not available

# Disable rate limiting for tests BEFORE importing app modules
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.core.security import create_access_token
from app.domain.enums.user_role import UserRole
from app.infrastructure.database.base import Base

# Import all models to ensure they're registered with Base.metadata
from app.infrastructure.database.models.comment import Comment  # noqa: F401
from app.infrastructure.database.models.community import Community  # noqa: F401
from app.infrastructure.database.models.membership import Membership  # noqa: F401
from app.infrastructure.database.models.post import Post  # noqa: F401
from app.infrastructure.database.models.reaction import Reaction  # noqa: F401
from app.infrastructure.database.models.university import University
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.verification import Verification  # noqa: F401
from app.main import app

# Test database URL - use DATABASE_URL from environment if available (CI), otherwise use local default
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://studybuddy:studybuddy_dev@localhost:5432/studybuddy_test"
)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for the test session."""
    policy = asyncio.get_event_loop_policy()
    return policy


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

    from app.infrastructure.database.session import get_db

    # Override the get_db dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as client:
        yield client

    # Clean up the override
    app.dependency_overrides.clear()


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


@pytest.fixture
def auth_headers() -> Callable[[UUID | str], dict[str, str]]:
    """Create authentication headers with JWT token.

    Returns a function that generates authorization headers for a given user ID.
    This fixture is used in integration tests to authenticate API requests.

    Returns:
        Callable: Function that takes a user_id and returns auth headers dict

    Example:
        ```python
        headers = auth_headers(test_user.id)
        response = await async_client.post("/api/v1/communities", headers=headers, json=data)
        ```
    """

    def _create_headers(user_id: UUID | str) -> dict[str, str]:
        """Create headers with JWT token for user.

        Args:
            user_id: User ID to encode in JWT token

        Returns:
            dict: Headers with Authorization bearer token
        """
        token = create_access_token(str(user_id))
        return {"Authorization": f"Bearer {token}"}

    return _create_headers
