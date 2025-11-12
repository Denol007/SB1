"""SQLAlchemy implementation of EventRegistrationRepository.

Provides database operations for event registrations using SQLAlchemy async ORM.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.event_registration_repository import (
    EventRegistrationRepository,
)
from app.core.exceptions import ConflictException
from app.domain.enums.registration_status import RegistrationStatus
from app.infrastructure.database.models.event_registration import EventRegistration


class SQLAlchemyEventRegistrationRepository(EventRegistrationRepository):
    """SQLAlchemy implementation of event registration repository.

    Handles all database operations for event registrations using async SQLAlchemy.

    Args:
        session: SQLAlchemy async database session.

    Example:
        >>> async with async_session() as session:
        ...     repository = SQLAlchemyEventRegistrationRepository(session)
        ...     registration = await repository.create(
        ...         event_id=event_uuid,
        ...         user_id=user_uuid,
        ...         status="registered"
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
        """
        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            status=status,
        )

        self.session.add(registration)

        try:
            await self.session.flush()
            await self.session.refresh(registration)
            return registration
        except IntegrityError as e:
            # Unique constraint violation on (event_id, user_id)
            if "unique" in str(e).lower():
                raise ConflictException(
                    f"User {user_id} is already registered for event {event_id}"
                ) from e
            raise

    async def get_by_id(self, registration_id: UUID) -> EventRegistration | None:
        """Retrieve event registration by ID.

        Args:
            registration_id: UUID of the registration to retrieve.

        Returns:
            EventRegistration instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(EventRegistration).where(EventRegistration.id == registration_id)
        )
        return result.scalar_one_or_none()

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
        """
        result = await self.session.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

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
        """
        registration = await self.get_by_id(registration_id)
        if not registration:
            raise ValueError(f"Registration {registration_id} not found")

        registration.status = RegistrationStatus(status)
        await self.session.commit()
        await self.session.refresh(registration)
        return registration

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
        """
        registration = await self.get_by_event_and_user(event_id, user_id)

        if not registration:
            return False

        await self.session.delete(registration)
        await self.session.flush()
        return True

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
        """
        query = select(EventRegistration).where(EventRegistration.event_id == event_id)

        if status:
            query = query.where(EventRegistration.status == status)

        query = query.order_by(EventRegistration.registered_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())

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
        """
        query = select(EventRegistration).where(EventRegistration.user_id == user_id)

        if status:
            query = query.where(EventRegistration.status == status)

        query = query.order_by(EventRegistration.registered_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

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
        """
        result = await self.session.execute(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.status == status,
            )
        )
        return result.scalar() or 0

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
        """
        result = await self.session.execute(
            select(EventRegistration)
            .where(
                EventRegistration.event_id == event_id,
                EventRegistration.status == "waitlisted",
            )
            .order_by(EventRegistration.registered_at)
            .limit(1)
        )
        return result.scalar_one_or_none()
