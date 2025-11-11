"""SQLAlchemy implementation of EventRepository.

Provides database operations for events using SQLAlchemy async ORM.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.event_repository import EventRepository
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.event_registration import EventRegistration


class SQLAlchemyEventRepository(EventRepository):
    """SQLAlchemy implementation of event repository.

    Handles all database operations for events using async SQLAlchemy.

    Args:
        session: SQLAlchemy async database session.

    Example:
        >>> async with async_session() as session:
        ...     repository = SQLAlchemyEventRepository(session)
        ...     event = await repository.create(
        ...         community_id=community_uuid,
        ...         creator_id=user_uuid,
        ...         title="Study Session",
        ...         description="Weekly review",
        ...         type="online",
        ...         start_time=datetime.now(),
        ...         end_time=datetime.now() + timedelta(hours=2),
        ...         status="published"
        ...     )
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

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
        """
        event = Event(
            community_id=community_id,
            creator_id=creator_id,
            title=title,
            description=description,
            type=type,
            location=location,
            start_time=start_time,
            end_time=end_time,
            participant_limit=participant_limit,
            status=status,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Retrieve event by ID.

        Args:
            event_id: UUID of the event to retrieve.

        Returns:
            Event instance if found and not deleted, None otherwise.
        """
        result = await self.session.execute(
            select(Event).where(
                Event.id == event_id,
                Event.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

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
        """
        event = await self.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found or deleted")

        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)

        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, event_id: UUID) -> None:
        """Soft delete an event.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            event_id: UUID of the event to delete.
        """
        event = await self.get_by_id(event_id)
        if event:
            event.deleted_at = datetime.now(UTC)
            await self.session.commit()

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
        """
        query = select(Event).where(
            Event.community_id == community_id,
            Event.deleted_at.is_(None),
        )

        if status:
            query = query.where(Event.status == status)

        query = (
            query.order_by(desc(Event.start_time)).offset((page - 1) * page_size).limit(page_size)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

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
        """
        result = await self.session.execute(
            select(Event)
            .where(
                Event.creator_id == creator_id,
                Event.deleted_at.is_(None),
            )
            .order_by(desc(Event.start_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def count_registered_participants(self, event_id: UUID) -> int:
        """Count registered participants for an event.

        Counts only registrations with status 'registered' (not waitlisted).

        Args:
            event_id: UUID of the event.

        Returns:
            Number of registered participants.
        """
        result = await self.session.execute(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.status == "registered",
            )
        )
        return result.scalar() or 0

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
        """
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Event)
            .where(
                Event.community_id == community_id,
                Event.status == "published",
                Event.start_time > now,
                Event.deleted_at.is_(None),
            )
            .order_by(Event.start_time)
            .limit(limit)
        )
        return list(result.scalars().all())
