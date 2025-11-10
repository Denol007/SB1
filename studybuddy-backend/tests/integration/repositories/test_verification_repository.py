"""Integration tests for VerificationRepository.

These tests verify the VerificationRepository implementation against a real database,
ensuring all verification data operations work correctly with PostgreSQL.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.domain.enums.user_role import UserRole
from app.domain.enums.verification_status import VerificationStatus
from app.infrastructure.database.models.university import University
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.verification import Verification
from app.infrastructure.repositories.verification_repository import (
    SQLAlchemyVerificationRepository,
)


@pytest.mark.asyncio
class TestVerificationRepository:
    """Test suite for VerificationRepository implementation."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession):
        """Create a VerificationRepository instance with database session.

        Args:
            db_session: Database session fixture.

        Returns:
            SQLAlchemyVerificationRepository: Repository instance for testing.
        """
        return SQLAlchemyVerificationRepository(db_session)

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user for verification tests.

        Args:
            db_session: Database session fixture.

        Returns:
            User: Created test user.
        """
        user = User(
            google_id=f"google_test_{uuid4()}",
            email=f"test_{uuid4()}@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_university(self, db_session: AsyncSession):
        """Create a test university for verification tests.

        Args:
            db_session: Database session fixture.

        Returns:
            University: Created test university.
        """
        university = University(
            name="Stanford University",
            domain="stanford.edu",
            country="USA",
        )
        db_session.add(university)
        await db_session.commit()
        await db_session.refresh(university)
        return university

    async def test_create_verification(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
    ):
        """Test creating a new verification record."""
        # Arrange
        verification = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_123",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        # Act
        created_verification = await repository.create(verification)

        # Assert
        assert created_verification.id is not None
        assert created_verification.user_id == test_user.id
        assert created_verification.university_id == test_university.id
        assert created_verification.email == test_user.email
        assert created_verification.token_hash == "hash_123"
        assert created_verification.status == VerificationStatus.PENDING
        assert created_verification.created_at is not None
        assert created_verification.verified_at is None

    async def test_get_by_token(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test retrieving a verification by token hash."""
        # Arrange
        verification = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="unique_token_hash",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        created_verification = await repository.create(verification)
        await db_session.commit()

        # Act
        retrieved_verification = await repository.get_by_token("unique_token_hash")

        # Assert
        assert retrieved_verification is not None
        assert retrieved_verification.id == created_verification.id
        assert retrieved_verification.token_hash == "unique_token_hash"

    async def test_get_by_token_not_found(self, repository: SQLAlchemyVerificationRepository):
        """Test that getting a non-existent token returns None."""
        # Act
        verification = await repository.get_by_token("nonexistent_token")

        # Assert
        assert verification is None

    async def test_get_by_user_and_university(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test retrieving a verification by user and university."""
        # Arrange
        verification = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_user_uni",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        await repository.create(verification)
        await db_session.commit()

        # Act
        retrieved_verification = await repository.get_by_user_and_university(
            test_user.id, test_university.id
        )

        # Assert
        assert retrieved_verification is not None
        assert retrieved_verification.user_id == test_user.id
        assert retrieved_verification.university_id == test_university.id

    async def test_get_by_user_and_university_returns_latest(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test that get_by_user_and_university returns the most recent verification."""
        # Arrange - Create two verifications for same user and university
        verification1 = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_old",
            status=VerificationStatus.EXPIRED,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        await repository.create(verification1)
        await db_session.commit()

        # Wait a moment to ensure different timestamps
        import asyncio

        await asyncio.sleep(0.01)

        verification2 = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_new",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        await repository.create(verification2)
        await db_session.commit()

        # Act
        retrieved_verification = await repository.get_by_user_and_university(
            test_user.id, test_university.id
        )

        # Assert - Should return the newer one
        assert retrieved_verification is not None
        assert retrieved_verification.token_hash == "hash_new"
        assert retrieved_verification.status == VerificationStatus.PENDING

    async def test_get_by_user_and_university_not_found(
        self, repository: SQLAlchemyVerificationRepository
    ):
        """Test that getting a non-existent user-university pair returns None."""
        # Act
        verification = await repository.get_by_user_and_university(uuid4(), uuid4())

        # Assert
        assert verification is None

    async def test_update_verification(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test updating a verification record."""
        # Arrange
        verification = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_update",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        created_verification = await repository.create(verification)
        await db_session.commit()

        # Modify the verification
        created_verification.status = VerificationStatus.VERIFIED
        created_verification.verified_at = datetime.now(UTC)

        # Act
        updated_verification = await repository.update(created_verification)
        await db_session.commit()

        # Assert
        assert updated_verification.status == VerificationStatus.VERIFIED
        assert updated_verification.verified_at is not None

    async def test_update_verification_not_found(
        self, repository: SQLAlchemyVerificationRepository
    ):
        """Test that updating a non-existent verification raises NotFoundException."""
        # Arrange
        verification = Verification(
            id=uuid4(),
            user_id=uuid4(),
            university_id=uuid4(),
            email="test@test.com",
            token_hash="nonexistent",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        # Act & Assert
        with pytest.raises(NotFoundException):
            await repository.update(verification)

    async def test_verification_status_transitions(
        self,
        repository: SQLAlchemyVerificationRepository,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test that verification status can transition through different states."""
        # Arrange
        verification = Verification(
            user_id=test_user.id,
            university_id=test_university.id,
            email=test_user.email,
            token_hash="hash_transition",
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        created_verification = await repository.create(verification)
        await db_session.commit()

        # Act & Assert - Transition to VERIFIED
        created_verification.status = VerificationStatus.VERIFIED
        created_verification.verified_at = datetime.now(UTC)
        updated = await repository.update(created_verification)
        await db_session.commit()
        assert updated.status == VerificationStatus.VERIFIED

        # Act & Assert - Could transition to EXPIRED (edge case)
        created_verification.status = VerificationStatus.EXPIRED
        updated = await repository.update(created_verification)
        await db_session.commit()
        assert updated.status == VerificationStatus.EXPIRED
