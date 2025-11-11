"""Event API endpoints.

This module provides REST API endpoints for event management:
- Create, read, update, delete events
- Register and unregister for events
- List events by community
- View event participants

Permissions:
- Any community member can view published events
- Moderators and admins can create events
- Event creators, moderators, and admins can update events
- Only event creators and admins can delete events
- Verified students and community members can register
- Users can unregister from events they're registered for
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.application.schemas.common import PaginatedResponse
from app.application.schemas.event import (
    EventCreate,
    EventDetailResponse,
    EventParticipantResponse,
    EventRegistrationResponse,
    EventResponse,
    EventUpdate,
)
from app.application.services.event_service import EventService
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.domain.enums.event_status import EventStatus
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.community_repository import SQLAlchemyCommunityRepository
from app.infrastructure.repositories.event_registration_repository import (
    SQLAlchemyEventRegistrationRepository,
)
from app.infrastructure.repositories.event_repository import SQLAlchemyEventRepository
from app.infrastructure.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter(tags=["Events"])


async def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    """Dependency for creating EventService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        EventService: Configured event service with dependencies.
    """
    event_repository = SQLAlchemyEventRepository(db)
    registration_repository = SQLAlchemyEventRegistrationRepository(db)
    membership_repository = SQLAlchemyMembershipRepository(db)
    community_repository = SQLAlchemyCommunityRepository(db)
    return EventService(
        event_repository, registration_repository, membership_repository, community_repository
    )


async def get_event_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyEventRepository:
    """Dependency for event repository.

    Args:
        db: Database session from dependency injection.

    Returns:
        SQLAlchemyEventRepository: Event repository instance.
    """
    return SQLAlchemyEventRepository(db)


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyUserRepository:
    """Dependency for user repository.

    Args:
        db: Database session from dependency injection.

    Returns:
        SQLAlchemyUserRepository: User repository instance.
    """
    return SQLAlchemyUserRepository(db)


async def get_registration_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyEventRegistrationRepository:
    """Dependency for registration repository.

    Args:
        db: Database session from dependency injection.

    Returns:
        SQLAlchemyEventRegistrationRepository: Registration repository instance.
    """
    return SQLAlchemyEventRegistrationRepository(db)


@router.get(
    "/communities/{community_id}/events",
    response_model=PaginatedResponse[EventResponse],
    summary="List events in a community",
    description="Get all events in a community with optional status filtering. "
    "Returns published events by default. Moderators can see all statuses.",
)
async def list_community_events(
    community_id: UUID,
    status: EventStatus | None = Query(
        default=None,
        description="Filter by event status",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    event_repo: SQLAlchemyEventRepository = Depends(get_event_repository),
) -> PaginatedResponse[EventResponse]:
    """List events in a community.

    Args:
        community_id: Community UUID.
        status: Optional status filter.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        current_user: Authenticated user.
        event_repo: Event repository.

    Returns:
        Paginated list of events.

    Raises:
        HTTPException: 404 if community not found.
    """
    try:
        # Get events from repository
        events = await event_repo.list_by_community(
            community_id=community_id,
            status=status.value if status else None,
            page=page,
            page_size=page_size,
        )

        # Convert to response models and add registered_count
        event_responses = []
        for event in events:
            registered_count = await event_repo.count_registered_participants(event.id)
            event_dict = {
                "id": event.id,
                "community_id": event.community_id,
                "creator_id": event.creator_id,
                "title": event.title,
                "description": event.description,
                "type": event.type,
                "location": event.location,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "participant_limit": event.participant_limit,
                "registered_count": registered_count,
                "status": event.status,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
            }
            event_responses.append(EventResponse(**event_dict))

        # Calculate total (simplified - in production, use count query)
        total = len(event_responses) + (page - 1) * page_size
        has_next = len(event_responses) == page_size

        return PaginatedResponse(
            items=event_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    except Exception as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}",
        )


@router.post(
    "/communities/{community_id}/events",
    response_model=EventDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Create a new event in a community. Requires moderator or admin role.",
)
async def create_event(
    community_id: UUID,
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    event_repo: SQLAlchemyEventRepository = Depends(get_event_repository),
) -> EventDetailResponse:
    """Create a new event.

    Args:
        community_id: Community UUID where event will be created.
        event_data: Event creation data.
        current_user: Authenticated user.
        event_service: Event service.
        event_repo: Event repository.

    Returns:
        Created event details.

    Raises:
        HTTPException: 403 if user lacks permission, 400 on validation error.
    """
    try:
        event = await event_service.create_event(
            user_id=current_user.id,
            community_id=community_id,
            event_data={
                "title": event_data.title,
                "description": event_data.description,
                "type": event_data.type.value,
                "start_time": event_data.start_time,
                "end_time": event_data.end_time,
                "location": event_data.location,
                "participant_limit": event_data.participant_limit,
                "status": event_data.status.value,
            },
        )

        # Get registered count
        registered_count = await event_repo.count_registered_participants(event.id)

        event_dict = {
            "id": event.id,
            "community_id": event.community_id,
            "creator_id": event.creator_id,
            "title": event.title,
            "description": event.description,
            "type": event.type,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "participant_limit": event.participant_limit,
            "registered_count": registered_count,
            "status": event.status,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

        return EventDetailResponse(**event_dict)

    except ForbiddenException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValidationException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )


@router.get(
    "/events/{event_id}",
    response_model=EventDetailResponse,
    summary="Get event details",
    description="Get detailed information about a specific event.",
)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_repo: SQLAlchemyEventRepository = Depends(get_event_repository),
) -> EventDetailResponse:
    """Get event details.

    Args:
        event_id: Event UUID.
        current_user: Authenticated user.
        event_repo: Event repository.

    Returns:
        Event details.

    Raises:
        HTTPException: 404 if event not found.
    """
    event = await event_repo.get_by_id(event_id)

    if not event:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Get registered count
    registered_count = await event_repo.count_registered_participants(event.id)

    event_dict = {
        "id": event.id,
        "community_id": event.community_id,
        "creator_id": event.creator_id,
        "title": event.title,
        "description": event.description,
        "type": event.type,
        "location": event.location,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "participant_limit": event.participant_limit,
        "registered_count": registered_count,
        "status": event.status,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }

    return EventDetailResponse(**event_dict)


@router.patch(
    "/events/{event_id}",
    response_model=EventDetailResponse,
    summary="Update an event",
    description="Update an event. Requires event creator, moderator, or admin role.",
)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    event_repo: SQLAlchemyEventRepository = Depends(get_event_repository),
) -> EventDetailResponse:
    """Update an event.

    Args:
        event_id: Event UUID.
        event_data: Update data.
        current_user: Authenticated user.
        event_service: Event service.
        event_repo: Event repository.

    Returns:
        Updated event details.

    Raises:
        HTTPException: 404 if not found, 403 if forbidden.
    """
    try:
        # Build update dict
        update_data = {}
        if event_data.title is not None:
            update_data["title"] = event_data.title
        if event_data.description is not None:
            update_data["description"] = event_data.description
        if event_data.type is not None:
            update_data["type"] = event_data.type.value
        if event_data.location is not None:
            update_data["location"] = event_data.location
        if event_data.start_time is not None:
            update_data["start_time"] = event_data.start_time
        if event_data.end_time is not None:
            update_data["end_time"] = event_data.end_time
        if event_data.participant_limit is not None:
            update_data["participant_limit"] = event_data.participant_limit
        if event_data.status is not None:
            update_data["status"] = event_data.status.value

        event = await event_service.update_event(
            event_id=event_id,
            user_id=current_user.id,
            update_data=update_data,
        )

        # Get registered count
        registered_count = await event_repo.count_registered_participants(event.id)

        event_dict = {
            "id": event.id,
            "community_id": event.community_id,
            "creator_id": event.creator_id,
            "title": event.title,
            "description": event.description,
            "type": event.type,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "participant_limit": event.participant_limit,
            "registered_count": registered_count,
            "status": event.status,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

        return EventDetailResponse(**event_dict)

    except NotFoundException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValidationException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/events/{event_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="Delete an event. Requires event creator or admin role.",
)
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> None:
    """Delete an event.

    Args:
        event_id: Event UUID.
        current_user: Authenticated user.
        event_service: Event service.

    Raises:
        HTTPException: 404 if not found, 403 if forbidden.
    """
    try:
        await event_service.delete_event(
            event_id=event_id,
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/events/{event_id}/register",
    response_model=EventRegistrationResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Register for an event",
    description="Register the current user for an event. "
    "Will be added to waitlist if event is at capacity.",
)
async def register_for_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventRegistrationResponse:
    """Register for an event.

    Args:
        event_id: Event UUID.
        current_user: Authenticated user.
        event_service: Event service.

    Returns:
        Registration details.

    Raises:
        HTTPException: 404 if not found, 403 if forbidden, 409 if already registered.
    """
    try:
        registration = await event_service.register_for_event(
            event_id=event_id,
            user_id=current_user.id,
        )

        return EventRegistrationResponse(
            event_id=registration.event_id,
            user_id=registration.user_id,
            status=registration.status,
            registered_at=registration.registered_at,
        )

    except NotFoundException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ConflictException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete(
    "/events/{event_id}/register",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Unregister from an event",
    description="Unregister the current user from an event. "
    "If user is registered, next waitlisted user will be auto-promoted.",
)
async def unregister_from_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> None:
    """Unregister from an event.

    Args:
        event_id: Event UUID.
        current_user: Authenticated user.
        event_service: Event service.

    Raises:
        HTTPException: 404 if not found or not registered.
    """
    try:
        await event_service.unregister_from_event(
            event_id=event_id,
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/events/{event_id}/participants",
    response_model=list[EventParticipantResponse],
    summary="List event participants",
    description="Get list of participants for an event. "
    "Can filter by status (registered, waitlisted, attended, no_show).",
)
async def list_event_participants(
    event_id: UUID,
    registration_status: str | None = Query(
        default=None,
        description="Filter by registration status",
    ),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    registration_repo: SQLAlchemyEventRegistrationRepository = Depends(get_registration_repository),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> list[EventParticipantResponse]:
    """List event participants.

    Args:
        event_id: Event UUID.
        registration_status: Optional status filter.
        current_user: Authenticated user.
        event_service: Event service.
        registration_repo: Registration repository.
        user_repo: User repository.

    Returns:
        List of participants.

    Raises:
        HTTPException: 404 if event not found.
    """
    try:
        # Get registrations
        registrations = await event_service.get_event_participants(
            event_id=event_id,
            status=registration_status,
        )

        # Build participant responses with user details
        participants = []
        for registration in registrations:
            user = await user_repo.get_by_id(registration.user_id)
            if user:
                participants.append(
                    EventParticipantResponse(
                        user_id=user.id,
                        email=user.email,
                        full_name=user.full_name,
                        status=registration.status,
                        registered_at=registration.registered_at,
                    )
                )

        return participants

    except NotFoundException as e:
        raise HTTPException(  # noqa: B904
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
