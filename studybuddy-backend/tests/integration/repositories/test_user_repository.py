"""Integration tests for UserRepository.

These tests verify the UserRepository implementation against a real database,
ensuring all CRUD operations work correctly with PostgreSQL.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.domain.enums.user_role import UserRole
from app.infrastructure.database.models.user import User
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository


@pytest.mark.asyncio
class TestUserRepository:
    """Test suite for UserRepository implementation."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession):
        """Create a UserRepository instance with database session.

        Args:
            db_session: Database session fixture.

        Returns:
            SQLAlchemyUserRepository: Repository instance for testing.
        """
        return SQLAlchemyUserRepository(db_session)

    async def test_create_user(self, repository: SQLAlchemyUserRepository):
        """Test creating a new user."""
        # Arrange
        user = User(
            google_id="google_123",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        # Act
        created_user = await repository.create(user)

        # Assert
        assert created_user.id is not None
        assert created_user.google_id == "google_123"
        assert created_user.email == "test@stanford.edu"
        assert created_user.name == "Test User"
        assert created_user.role == UserRole.STUDENT
        assert created_user.created_at is not None
        assert created_user.updated_at is not None
        assert created_user.deleted_at is None

    async def test_create_user_duplicate_email(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test that creating a user with duplicate email raises ConflictException."""
        # Arrange
        user1 = User(
            google_id="google_123",
            email="duplicate@stanford.edu",
            name="User 1",
            role=UserRole.STUDENT,
        )
        await repository.create(user1)
        await db_session.commit()

        user2 = User(
            google_id="google_456",
            email="duplicate@stanford.edu",
            name="User 2",
            role=UserRole.STUDENT,
        )

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await repository.create(user2)

        assert "email" in str(exc_info.value).lower()

    async def test_create_user_duplicate_google_id(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test that creating a user with duplicate google_id raises ConflictException."""
        # Arrange
        user1 = User(
            google_id="google_duplicate",
            email="user1@stanford.edu",
            name="User 1",
            role=UserRole.STUDENT,
        )
        await repository.create(user1)
        await db_session.commit()

        user2 = User(
            google_id="google_duplicate",
            email="user2@stanford.edu",
            name="User 2",
            role=UserRole.STUDENT,
        )

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await repository.create(user2)

        assert "google" in str(exc_info.value).lower()

    async def test_get_by_id(self, repository: SQLAlchemyUserRepository, db_session: AsyncSession):
        """Test retrieving a user by ID."""
        # Arrange
        user = User(
            google_id="google_get_by_id",
            email="getbyid@stanford.edu",
            name="Get By ID User",
            role=UserRole.STUDENT,
        )
        created_user = await repository.create(user)
        await db_session.commit()

        # Act
        retrieved_user = await repository.get_by_id(created_user.id)

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "getbyid@stanford.edu"

    async def test_get_by_id_not_found(self, repository: SQLAlchemyUserRepository):
        """Test that getting a non-existent user returns None."""
        # Act
        user = await repository.get_by_id(uuid4())

        # Assert
        assert user is None

    async def test_get_by_id_soft_deleted(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test that getting a soft-deleted user returns None."""
        # Arrange
        user = User(
            google_id="google_deleted",
            email="deleted@stanford.edu",
            name="Deleted User",
            role=UserRole.STUDENT,
        )
        created_user = await repository.create(user)
        await db_session.commit()

        # Soft delete the user
        await repository.delete(created_user.id)
        await db_session.commit()

        # Act
        retrieved_user = await repository.get_by_id(created_user.id)

        # Assert
        assert retrieved_user is None

    async def test_get_by_email(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test retrieving a user by email."""
        # Arrange
        user = User(
            google_id="google_email",
            email="getbyemail@stanford.edu",
            name="Get By Email User",
            role=UserRole.STUDENT,
        )
        await repository.create(user)
        await db_session.commit()

        # Act
        retrieved_user = await repository.get_by_email("getbyemail@stanford.edu")

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email == "getbyemail@stanford.edu"

    async def test_get_by_email_case_insensitive(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test that email search is case-insensitive."""
        # Arrange
        user = User(
            google_id="google_case",
            email="CaseTest@Stanford.EDU",
            name="Case Test User",
            role=UserRole.STUDENT,
        )
        await repository.create(user)
        await db_session.commit()

        # Act
        retrieved_user = await repository.get_by_email("casetest@stanford.edu")

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email == "CaseTest@Stanford.EDU"

    async def test_get_by_email_not_found(self, repository: SQLAlchemyUserRepository):
        """Test that getting a non-existent email returns None."""
        # Act
        user = await repository.get_by_email("nonexistent@example.com")

        # Assert
        assert user is None

    async def test_get_by_google_id(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test retrieving a user by Google ID."""
        # Arrange
        user = User(
            google_id="google_unique_123",
            email="googleid@stanford.edu",
            name="Google ID User",
            role=UserRole.STUDENT,
        )
        await repository.create(user)
        await db_session.commit()

        # Act
        retrieved_user = await repository.get_by_google_id("google_unique_123")

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.google_id == "google_unique_123"

    async def test_get_by_google_id_not_found(self, repository: SQLAlchemyUserRepository):
        """Test that getting a non-existent Google ID returns None."""
        # Act
        user = await repository.get_by_google_id("nonexistent_google_id")

        # Assert
        assert user is None

    async def test_update_user(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test updating a user's information."""
        # Arrange
        user = User(
            google_id="google_update",
            email="update@stanford.edu",
            name="Original Name",
            role=UserRole.STUDENT,
        )
        created_user = await repository.create(user)
        await db_session.commit()

        # Modify the user
        created_user.name = "Updated Name"
        created_user.bio = "New bio"

        # Act
        updated_user = await repository.update(created_user)
        await db_session.commit()

        # Assert
        assert updated_user.name == "Updated Name"
        assert updated_user.bio == "New bio"
        assert updated_user.updated_at > created_user.created_at

    async def test_update_user_not_found(self, repository: SQLAlchemyUserRepository):
        """Test that updating a non-existent user raises NotFoundException."""
        # Arrange
        user = User(
            id=uuid4(),
            google_id="google_nonexistent",
            email="nonexistent@stanford.edu",
            name="Nonexistent User",
            role=UserRole.STUDENT,
        )

        # Act & Assert
        with pytest.raises(NotFoundException):
            await repository.update(user)

    async def test_delete_user(
        self, repository: SQLAlchemyUserRepository, db_session: AsyncSession
    ):
        """Test soft deleting a user."""
        # Arrange
        user = User(
            google_id="google_delete",
            email="delete@stanford.edu",
            name="Delete User",
            role=UserRole.STUDENT,
        )
        created_user = await repository.create(user)
        await db_session.commit()

        # Act
        await repository.delete(created_user.id)
        await db_session.commit()

        # Assert - user should not be retrievable
        retrieved_user = await repository.get_by_id(created_user.id)
        assert retrieved_user is None

        # But the user should still exist in the database with deleted_at set
        from sqlalchemy import select

        stmt = select(User).where(User.id == created_user.id)
        result = await db_session.execute(stmt)
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None

    async def test_delete_user_not_found(self, repository: SQLAlchemyUserRepository):
        """Test that deleting a non-existent user raises NotFoundException."""
        # Act & Assert
        with pytest.raises(NotFoundException):
            await repository.delete(uuid4())
