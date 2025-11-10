"""University repository implementation.

This module provides the concrete implementation of the UniversityRepository interface
using SQLAlchemy async queries for PostgreSQL database operations.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.university_repository import UniversityRepository
from app.infrastructure.database.models.university import University


class SQLAlchemyUniversityRepository(UniversityRepository):
    """SQLAlchemy implementation of the UniversityRepository interface.

    This repository handles all university data query operations using SQLAlchemy's
    async API with PostgreSQL. Universities are generally read-only reference data.

    Args:
        session: AsyncSession instance for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

    async def get_by_domain(self, domain: str) -> University | None:
        """Retrieve a university by its email domain.

        Args:
            domain: Email domain to search for (e.g., "stanford.edu").
                   Should be case-insensitive.

        Returns:
            University | None: The university if found, None otherwise.

        Note:
            This method is used during student verification to match email addresses
            to their respective universities. Domains are expected to be unique.
        """
        stmt = select(University).where(University.domain.ilike(domain))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[University]:
        """Retrieve all universities in the system.

        Returns:
            list[University]: List of all university records, ordered by name.

        Note:
            This method is typically used for displaying university selection options
            during the verification process. Consider implementing pagination if the
            list grows very large.
        """
        stmt = select(University).order_by(University.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
