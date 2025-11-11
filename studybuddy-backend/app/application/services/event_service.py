"""Event service for business logic.

Handles:
- Event creation, updates, and deletion (soft delete)
- Event registration with capacity limits and waitlist
- Event unregistration with auto-promotion from waitlist
- Participant listing
- Event status changes
- Permission checks (creator, moderator, admin)
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.application.interfaces.community_repository import CommunityRepository
from app.application.interfaces.event_registration_repository import (
    EventRegistrationRepository,
)
from app.application.interfaces.event_repository import EventRepository
from app.application.interfaces.membership_repository import MembershipRepository
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.event_registration import EventRegistration


class EventService:
    """Service for event and registration management.

    This service implements business logic for event operations,
    including creation, updates, deletion, registration, and participant management.

    Example:
        >>> service = EventService(event_repo, registration_repo, membership_repo, community_repo)
        >>> event = await service.create_event(
        ...     user_id=user_uuid,
        ...     community_id=community_uuid,
        ...     event_data={"title": "Study Session", ...}
        ... )
    """

    def __init__(
        self,
        event_repository: EventRepository,
        registration_repository: EventRegistrationRepository,
        membership_repository: MembershipRepository,
        community_repository: CommunityRepository,
    ):
        """Initialize the event service.

        Args:
            event_repository: Repository for event data access.
            registration_repository: Repository for registration data access.
            membership_repository: Repository for membership data access.
            community_repository: Repository for community data access.
        """
        self.event_repository = event_repository
        self.registration_repository = registration_repository
        self.membership_repository = membership_repository
        self.community_repository = community_repository

    async def create_event(
        self,
        user_id: UUID,
        community_id: UUID,
        event_data: dict[str, Any],
    ) -> Event:
        """Create a new event in a community.

        User must be a moderator or admin to create events.

        Args:
            user_id: UUID of the user creating the event.
            community_id: UUID of the community.
            event_data: Event data (title, description, type, start_time, end_time, etc).

        Returns:
            Created Event instance.

        Raises:
            HTTPException 403: If user is not a moderator or admin.
            HTTPException 400: If validation fails.

        Example:
            >>> event = await service.create_event(
            ...     user_id=user_uuid,
            ...     community_id=community_uuid,
            ...     event_data={
            ...         "title": "Python Workshop",
            ...         "description": "Learn Python basics",
            ...         "type": "online",
            ...         "start_time": datetime.now() + timedelta(days=7),
            ...         "end_time": datetime.now() + timedelta(days=7, hours=2),
            ...         "participant_limit": 50
            ...     }
            ... )
        """
        # Verify user is a moderator or admin
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this community to create events",
            )

        if membership.role not in (MembershipRole.MODERATOR, MembershipRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators and admins can create events",
            )

        # Validate start_time is in the future
        start_time = event_data.get("start_time")
        if start_time and start_time <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event start time must be in the future",
            )

        # Validate end_time is after start_time
        end_time = event_data.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be after start time",
            )

        # Create the event
        event = await self.event_repository.create(
            community_id=community_id,
            creator_id=user_id,
            title=event_data["title"],
            description=event_data["description"],
            type=event_data["type"],
            start_time=start_time,
            end_time=end_time,
            status=event_data.get("status", "published"),
            location=event_data.get("location"),
            participant_limit=event_data.get("participant_limit"),
        )

        return event

    async def update_event(
        self,
        event_id: UUID,
        user_id: UUID,
        update_data: dict[str, Any],
    ) -> Event:
        """Update an event.

        User must be the creator, a moderator, or an admin.

        Args:
            event_id: UUID of the event to update.
            user_id: UUID of the user making the update.
            update_data: Fields to update.

        Returns:
            Updated Event instance.

        Raises:
            HTTPException 404: If event doesn't exist.
            HTTPException 403: If user lacks permission.

        Example:
            >>> event = await service.update_event(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid,
            ...     update_data={"title": "Updated Title", "participant_limit": 100}
            ... )
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Check permissions: creator, moderator, or admin
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=event.community_id,
        )

        is_creator = event.creator_id == user_id
        is_moderator_or_admin = membership and membership.role in (
            MembershipRole.MODERATOR,
            MembershipRole.ADMIN,
        )

        if not (is_creator or is_moderator_or_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator, moderators, or admins can update this event",
            )

        # Update the event
        updated_event = await self.event_repository.update(
            event_id=event_id,
            **update_data,
        )

        return updated_event

    async def delete_event(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete an event (soft delete).

        User must be the creator, a moderator, or an admin.

        Args:
            event_id: UUID of the event to delete.
            user_id: UUID of the user requesting deletion.

        Raises:
            HTTPException 404: If event doesn't exist.
            HTTPException 403: If user lacks permission.

        Example:
            >>> await service.delete_event(event_id=event_uuid, user_id=user_uuid)
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Check permissions: creator or admin only
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=event.community_id,
        )

        is_creator = event.creator_id == user_id
        is_admin = membership and membership.role == MembershipRole.ADMIN

        if not (is_creator or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator or admins can delete this event",
            )

        await self.event_repository.delete(event_id)

    async def register_for_event(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> EventRegistration:
        """Register a user for an event.

        Handles capacity limits and waitlist placement automatically.

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user registering.

        Returns:
            Created EventRegistration instance.

        Raises:
            HTTPException 404: If event doesn't exist.
            HTTPException 403: If user is not a community member.
            HTTPException 409: If user is already registered.
            HTTPException 400: If event is completed or cancelled.

        Example:
            >>> registration = await service.register_for_event(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid
            ... )
        """
        # Get the event
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Verify user is a community member
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=event.community_id,
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this community to register for events",
            )

        # Check if event is still open for registration
        if event.status in ("completed", "cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot register for {event.status} event",
            )

        # Check if user is already registered
        existing_registration = await self.registration_repository.get_by_event_and_user(
            event_id=event_id,
            user_id=user_id,
        )
        if existing_registration:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already registered for this event",
            )

        # Determine registration status based on capacity
        registration_status = "registered"

        if event.participant_limit is not None:
            # Count current registered participants
            registered_count = await self.registration_repository.count_by_event_and_status(
                event_id=event_id,
                status="registered",
            )

            if registered_count >= event.participant_limit:
                registration_status = "waitlisted"

        # Create the registration
        registration = await self.registration_repository.create(
            event_id=event_id,
            user_id=user_id,
            status=registration_status,
        )

        return registration

    async def unregister_from_event(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> None:
        """Unregister a user from an event.

        Automatically promotes the first waitlisted user if applicable.

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user unregistering.

        Raises:
            HTTPException 404: If event or registration doesn't exist.

        Example:
            >>> await service.unregister_from_event(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid
            ... )
        """
        # Get the event
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Get the registration
        registration = await self.registration_repository.get_by_event_and_user(
            event_id=event_id,
            user_id=user_id,
        )
        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not registered for this event",
            )

        # Delete the registration
        await self.registration_repository.delete(
            event_id=event_id,
            user_id=user_id,
        )

        # If user was registered (not waitlisted), promote first waitlisted user
        if registration.status == "registered":
            first_waitlisted = await self.registration_repository.get_first_waitlisted(
                event_id=event_id
            )
            if first_waitlisted:
                await self.registration_repository.update_status(
                    registration_id=first_waitlisted.id,
                    status="registered",
                )

    async def get_event_participants(
        self,
        event_id: UUID,
        status: str = "registered",
    ) -> list[EventRegistration]:
        """Get participants for an event by status.

        Args:
            event_id: UUID of the event.
            status: Registration status filter (registered, waitlisted, attended, no_show).

        Returns:
            List of EventRegistration instances.

        Example:
            >>> participants = await service.get_event_participants(
            ...     event_id=event_uuid,
            ...     status="registered"
            ... )
        """
        registrations = await self.registration_repository.list_by_event(
            event_id=event_id,
            status=status,
        )
        return registrations

    async def change_event_status(
        self,
        event_id: UUID,
        user_id: UUID,
        new_status: str,
    ) -> Event:
        """Change the status of an event.

        User must be the creator, a moderator, or an admin.
        Validates status transitions (e.g., cannot change completed event back to published).

        Args:
            event_id: UUID of the event.
            user_id: UUID of the user changing status.
            new_status: New status (draft, published, completed, cancelled).

        Returns:
            Updated Event instance.

        Raises:
            HTTPException 404: If event doesn't exist.
            HTTPException 403: If user lacks permission.
            HTTPException 400: If status transition is invalid.

        Example:
            >>> event = await service.change_event_status(
            ...     event_id=event_uuid,
            ...     user_id=user_uuid,
            ...     new_status="cancelled"
            ... )
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Check permissions: creator, moderator, or admin
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=event.community_id,
        )

        is_creator = event.creator_id == user_id
        is_moderator_or_admin = membership and membership.role in (
            MembershipRole.MODERATOR,
            MembershipRole.ADMIN,
        )

        if not (is_creator or is_moderator_or_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator, moderators, or admins can change event status",
            )

        # Validate status transitions
        # Cannot change completed event to published or draft
        if event.status == "completed" and new_status in ("published", "draft"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change completed event status to published or draft",
            )

        # Update the status
        updated_event = await self.event_repository.update(
            event_id=event_id,
            status=new_status,
        )

        return updated_event
