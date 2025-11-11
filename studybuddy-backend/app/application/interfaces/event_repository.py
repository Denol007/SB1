"""Event repository interface.

Defines the contract for event data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.infrastructure.database.models.event import Event


class EventRepository(ABC):
    """Abstract repository for event data access operations.

    This interface defines all database operations for events,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyEventRepository(session)
        >>> event = await repository.create(
        ...     community_id=community_uuid,
        ...     creator_id=user_uuid,
        ...     title="Study Session",
        ...     description="Weekly calculus review",
        ...     type="online",
        ...     start_time=datetime.now(),
        ...     end_time=datetime.now() + timedelta(hours=2),
        ...     status="published"
        ... )
    """

    @abstractmethod
    async def create(
        self,
        community_id: UUID,
        creator_id: UUID,
        title: str,
        description: str,
        type: str,
        start_time: datetime,
        end_time: datetime,
        status: str,
        location: str | None = None,
        participant_limit: int | None = None,
    ) -> Event:
        """Create a new event.

        Args:
            community_id: UUID of the community hosting the event.
            creator_id: UUID of the user creating the event.
            title: Event title (max 200 characters).
            description: Detailed event description.
            type: Event type (online, offline, hybrid).
            start_time: Event start date and time.
            end_time: Event end date and time.
            status: Event status (draft, published, completed, cancelled).
            location: Event location or meeting link (optional).
            participant_limit: Maximum number of participants (None = unlimited).

        Returns:
            Created Event instance with generated ID.

        Example:
            >>> event = await repository.create(
            ...     community_id=uuid,
            ...     creator_id=uuid,
            ...     title="Code Review Session",
            ...     description="Review algorithms homework",
            ...     type="online",
            ...     start_time=datetime.now(),
            ...     end_time=datetime.now() + timedelta(hours=1),
            ...     status="published",
            ...     location="https://meet.google.com/abc-def-ghi"
            ... )
        """
        pass

    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Retrieve event by ID.

        Args:
            event_id: UUID of the event to retrieve.

        Returns:
            Event instance if found and not deleted, None otherwise.

        Example:
            >>> event = await repository.get_by_id(uuid)
            >>> if event:
            ...     print(event.title)
        """
        pass

    @abstractmethod
    async def update(
        self,
        event_id: UUID,
        **kwargs: str | datetime | int | None,
    ) -> Event:
        """Update an event.

        Args:
            event_id: UUID of the event to update.
            **kwargs: Fields to update (title, description, type, location,
                     start_time, end_time, participant_limit, status).

        Returns:
            Updated Event instance.

        Raises:
            ValueError: If event_id is invalid or event is deleted.

        Example:
            >>> event = await repository.update(
            ...     event_id=uuid,
            ...     title="Updated Title",
            ...     participant_limit=50
            ... )
        """
        pass

    @abstractmethod
    async def delete(self, event_id: UUID) -> None:
        """Soft delete an event.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            event_id: UUID of the event to delete.

        Example:
            >>> await repository.delete(uuid)
        """
        pass

    @abstractmethod
    async def list_by_community(
        self,
        community_id: UUID,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Event]:
        """List events in a community with optional filtering.

        Returns events sorted by start_time in descending order.
        Excludes soft-deleted events.

        Args:
            community_id: UUID of the community.
            status: Optional status filter (published, draft, completed, cancelled).
            page: Page number (1-indexed).
            page_size: Number of events per page.

        Returns:
            List of Event instances for the requested page.

        Example:
            >>> events = await repository.list_by_community(
            ...     community_id=uuid,
            ...     status="published",
            ...     page=1,
            ...     page_size=10
            ... )
        """
        pass

    @abstractmethod
    async def list_by_creator(
        self,
        creator_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Event]:
        """List events created by a specific user.

        Returns events sorted by start_time in descending order.
        Excludes soft-deleted events.

        Args:
            creator_id: UUID of the event creator.
            page: Page number (1-indexed).
            page_size: Number of events per page.

        Returns:
            List of Event instances for the requested page.

        Example:
            >>> events = await repository.list_by_creator(
            ...     creator_id=uuid,
            ...     page=1
            ... )
        """
        pass

    @abstractmethod
    async def count_registered_participants(self, event_id: UUID) -> int:
        """Count registered participants for an event.

        Counts only registrations with status 'registered' (not waitlisted).

        Args:
            event_id: UUID of the event.

        Returns:
            Number of registered participants.

        Example:
            >>> count = await repository.count_registered_participants(uuid)
            >>> print(f"Registered: {count}")
        """
        pass

    @abstractmethod
    async def get_upcoming_events(
        self,
        community_id: UUID,
        limit: int = 10,
    ) -> list[Event]:
        """Get upcoming published events for a community.

        Returns events with start_time in the future, sorted by start_time.
        Only includes published events. Excludes soft-deleted events.

        Args:
            community_id: UUID of the community.
            limit: Maximum number of events to return.

        Returns:
            List of upcoming Event instances.

        Example:
            >>> events = await repository.get_upcoming_events(
            ...     community_id=uuid,
            ...     limit=5
            ... )
        """
        pass
