"""Integration tests for UniversityRepository.

These tests verify the UniversityRepository implementation against a real database,
ensuring all university query operations work correctly with PostgreSQL.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.university import University
from app.infrastructure.repositories.university_repository import (
    SQLAlchemyUniversityRepository,
)


@pytest.mark.asyncio
class TestUniversityRepository:
    """Test suite for UniversityRepository implementation."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession):
        """Create a UniversityRepository instance with database session.

        Args:
            db_session: Database session fixture.

        Returns:
            SQLAlchemyUniversityRepository: Repository instance for testing.
        """
        return SQLAlchemyUniversityRepository(db_session)

    @pytest_asyncio.fixture
    async def sample_universities(self, db_session: AsyncSession):
        """Create sample universities for testing.

        Args:
            db_session: Database session fixture.

        Returns:
            list[University]: List of created universities.
        """
        universities = [
            University(
                name="Stanford University",
                domain="stanford.edu",
                country="USA",
                logo_url="https://example.com/stanford.png",
            ),
            University(
                name="Massachusetts Institute of Technology",
                domain="mit.edu",
                country="USA",
                logo_url="https://example.com/mit.png",
            ),
            University(
                name="Harvard University",
                domain="harvard.edu",
                country="USA",
                logo_url="https://example.com/harvard.png",
            ),
        ]

        for university in universities:
            db_session.add(university)

        await db_session.commit()

        for university in universities:
            await db_session.refresh(university)

        return universities

    async def test_get_by_domain(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test retrieving a university by domain."""
        # Act
        university = await repository.get_by_domain("stanford.edu")

        # Assert
        assert university is not None
        assert university.name == "Stanford University"
        assert university.domain == "stanford.edu"
        assert university.country == "USA"

    async def test_get_by_domain_case_insensitive(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test that domain search is case-insensitive."""
        # Act
        university = await repository.get_by_domain("STANFORD.EDU")

        # Assert
        assert university is not None
        assert university.name == "Stanford University"
        assert university.domain == "stanford.edu"

    async def test_get_by_domain_with_mixed_case(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test domain search with mixed case."""
        # Act
        university = await repository.get_by_domain("StAnFoRd.EdU")

        # Assert
        assert university is not None
        assert university.name == "Stanford University"

    async def test_get_by_domain_not_found(self, repository: SQLAlchemyUniversityRepository):
        """Test that getting a non-existent domain returns None."""
        # Act
        university = await repository.get_by_domain("nonexistent.edu")

        # Assert
        assert university is None

    async def test_list_all(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test listing all universities."""
        # Act
        universities = await repository.list_all()

        # Assert
        assert len(universities) == 3
        # Should be ordered by name
        assert universities[0].name == "Harvard University"
        assert universities[1].name == "Massachusetts Institute of Technology"
        assert universities[2].name == "Stanford University"

    async def test_list_all_empty(
        self, repository: SQLAlchemyUniversityRepository, db_session: AsyncSession
    ):
        """Test listing universities when none exist."""
        # Act
        universities = await repository.list_all()

        # Assert
        assert universities == []

    async def test_list_all_returns_all_fields(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test that list_all returns complete university records."""
        # Act
        universities = await repository.list_all()

        # Assert
        for university in universities:
            assert university.id is not None
            assert university.name is not None
            assert university.domain is not None
            assert university.country is not None
            assert university.created_at is not None
            assert university.updated_at is not None

    async def test_get_by_domain_returns_complete_record(
        self,
        repository: SQLAlchemyUniversityRepository,
        sample_universities: list[University],
    ):
        """Test that get_by_domain returns complete university record."""
        # Act
        university = await repository.get_by_domain("mit.edu")

        # Assert
        assert university is not None
        assert university.id is not None
        assert university.name == "Massachusetts Institute of Technology"
        assert university.domain == "mit.edu"
        assert university.country == "USA"
        assert university.logo_url == "https://example.com/mit.png"
        assert university.created_at is not None
        assert university.updated_at is not None
