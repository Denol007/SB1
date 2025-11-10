"""University repository interface.

This module defines the abstract interface for university data access operations,
following the hexagonal architecture pattern. Concrete implementations will
be provided in the infrastructure layer.
"""

from abc import ABC, abstractmethod

from app.infrastructure.database.models.university import University


class UniversityRepository(ABC):
    """Abstract repository interface for university data access.

    Defines the contract for all university-related data operations. Implementations
    must provide async methods for querying university information.
    """

    @abstractmethod
    async def get_by_domain(self, domain: str) -> University | None:
        """Retrieve a university by its email domain.

        Args:
            domain: Email domain to search for (e.g., "stanford.edu").
                   Should be case-insensitive.

        Returns:
            Optional[University]: The university if found, None otherwise.

        Note:
            This method is used during student verification to match email addresses
            to their respective universities. Domains are expected to be unique.
        """
        pass

    @abstractmethod
    async def list_all(self) -> list[University]:
        """Retrieve all universities in the system.

        Returns:
            List[University]: List of all university records, ordered by name.

        Note:
            This method is typically used for displaying university selection options
            during the verification process. Consider implementing pagination if the
            list grows very large.
        """
        pass
