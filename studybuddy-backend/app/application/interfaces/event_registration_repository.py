"""Event registration repository interface.

Defines the contract for event registration data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.infrastructure.database.models.event_registration import EventRegistration


class EventRegistrationRepository(ABC):
    """Abstract repository for event registration data access operations.

    This interface defines all database operations for event registrations,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyEventRegistrationRepository(session)
        >>> registration = await repository.create(
        ...     event_id=event_uuid,
        ...     user_id=user_uuid,
        ...     status="registered"
        ... )
    """

    @abstractmethod
    async def create(
        self,
        event_id: UUID,
        user_id: UUID,
        status: str,
    ) -> EventRegistration:
        """Create a new event registration.

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user registering.
            status: Registration status (registered, waitlisted, attended, no_show).

        Returns:
            Created EventRegistration instance with generated ID.

        Raises:
            ConflictException: If user is already registered for this event.

        Example:
            >>> registration = await repository.create(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid,
            ...     status="registered"
            ... )
        """
        pass

    @abstractmethod
    async def get_by_id(self, registration_id: UUID) -> EventRegistration | None:
        """Retrieve event registration by ID.

        Args:
            registration_id: UUID of the registration to retrieve.

        Returns:
            EventRegistration instance if found, None otherwise.

        Example:
            >>> registration = await repository.get_by_id(uuid)
            >>> if registration:
            ...     print(registration.status)
        """
        pass

    @abstractmethod
    async def get_by_event_and_user(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> EventRegistration | None:
        """Get a user's registration for a specific event.

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user.

        Returns:
            EventRegistration instance if found, None otherwise.

        Example:
            >>> registration = await repository.get_by_event_and_user(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid
            ... )
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        registration_id: UUID,
        status: str,
    ) -> EventRegistration:
        """Update registration status.

        Args:
            registration_id: UUID of the registration to update.
            status: New registration status (registered, waitlisted, attended, no_show).

        Returns:
            Updated EventRegistration instance.

        Raises:
            ValueError: If registration_id is invalid.

        Example:
            >>> registration = await repository.update_status(
            ...     registration_id=uuid,
            ...     status="attended"
            ... )
        """
        pass

    @abstractmethod
    async def delete(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete an event registration.

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user.

        Returns:
            True if registration was deleted, False if not found.

        Example:
            >>> deleted = await repository.delete(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid
            ... )
        """
        pass

    @abstractmethod
    async def list_by_event(
        self,
        event_id: UUID,
        status: str | None = None,
    ) -> list[EventRegistration]:
        """List registrations for an event.

        Returns registrations sorted by registered_at (oldest first).

        Args:
            event_id: UUID of the event.
            status: Optional status filter (registered, waitlisted, attended, no_show).

        Returns:
            List of EventRegistration instances.

        Example:
            >>> registrations = await repository.list_by_event(
            ...     event_id=uuid,
            ...     status="registered"
            ... )
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[EventRegistration]:
        """List registrations for a user.

        Returns registrations sorted by registered_at (newest first).

        Args:
            user_id: UUID of the user.
            status: Optional status filter (registered, waitlisted, attended, no_show).

        Returns:
            List of EventRegistration instances.

        Example:
            >>> registrations = await repository.list_by_user(
            ...     user_id=uuid,
            ...     status="registered"
            ... )
        """
        pass

    @abstractmethod
    async def count_by_event_and_status(
        self,
        event_id: UUID,
        status: str,
    ) -> int:
        """Count registrations for an event by status.

        Args:
            event_id: UUID of the event.
            status: Registration status to count.

        Returns:
            Number of registrations with the specified status.

        Example:
            >>> count = await repository.count_by_event_and_status(
            ...     event_id=uuid,
            ...     status="registered"
            ... )
        """
        pass

    @abstractmethod
    async def get_first_waitlisted(
        self,
        event_id: UUID,
    ) -> EventRegistration | None:
        """Get the first waitlisted registration for an event.

        Returns the oldest waitlisted registration (FIFO).

        Args:
            event_id: UUID of the event.

        Returns:
            First waitlisted EventRegistration instance, or None if no waitlist.

        Example:
            >>> registration = await repository.get_first_waitlisted(uuid)
            >>> if registration:
            ...     # Promote to registered status
            ...     await repository.update_status(registration.id, "registered")
        """
        pass
