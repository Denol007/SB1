"""Event schemas (DTOs) for request/response validation.

Pydantic models for:
- Event creation and updates
- Event list and detail responses
- Event registration responses
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.domain.enums.event_status import EventStatus
from app.domain.enums.event_type import EventType


class EventCreate(BaseModel):
    """Schema for creating a new event.

    Used when creating an event with all required fields.

    Attributes:
        title: Event title (1-200 characters).
        description: Event description (1-5000 characters).
        type: Event type (online, offline, hybrid).
        location: Event location or meeting link (optional).
        start_time: Event start date and time.
        end_time: Event end date and time.
        participant_limit: Maximum number of participants (None = unlimited).
        status: Event status (defaults to draft).

    Example:
        >>> event = EventCreate(
        ...     title="Study Session",
        ...     description="Weekly calculus review",
        ...     type=EventType.ONLINE,
        ...     location="https://zoom.us/j/123",
        ...     start_time=datetime(2025, 12, 1, 14, 0),
        ...     end_time=datetime(2025, 12, 1, 16, 0),
        ...     participant_limit=20,
        ...     status=EventStatus.PUBLISHED
        ... )
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Event title",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Event description",
    )
    type: EventType = Field(
        ...,
        description="Event type (online, offline, hybrid)",
    )
    location: str | None = Field(
        default=None,
        max_length=500,
        description="Event location or meeting link",
    )
    start_time: datetime = Field(
        ...,
        description="Event start date and time",
    )
    end_time: datetime = Field(
        ...,
        description="Event end date and time",
    )
    participant_limit: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of participants (None = unlimited)",
    )
    status: EventStatus = Field(
        default=EventStatus.DRAFT,
        description="Event status",
    )

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Validate that end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Weekly Study Session",
                "description": "Join us for our weekly calculus study session. We'll review the latest chapters and work through practice problems together.",
                "type": "online",
                "location": "https://zoom.us/j/123456789",
                "start_time": "2025-12-01T14:00:00Z",
                "end_time": "2025-12-01T16:00:00Z",
                "participant_limit": 20,
                "status": "published",
            }
        }
    }


class EventUpdate(BaseModel):
    """Schema for updating an existing event.

    All fields are optional. Only provided fields will be updated.

    Attributes:
        title: Updated event title.
        description: Updated event description.
        type: Updated event type.
        location: Updated event location.
        start_time: Updated start time.
        end_time: Updated end time.
        participant_limit: Updated participant limit.
        status: Updated event status.

    Example:
        >>> update = EventUpdate(
        ...     title="Updated Title",
        ...     participant_limit=30
        ... )
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated event title",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="Updated event description",
    )
    type: EventType | None = Field(
        default=None,
        description="Updated event type",
    )
    location: str | None = Field(
        default=None,
        max_length=500,
        description="Updated event location or meeting link",
    )
    start_time: datetime | None = Field(
        default=None,
        description="Updated event start time",
    )
    end_time: datetime | None = Field(
        default=None,
        description="Updated event end time",
    )
    participant_limit: int | None = Field(
        default=None,
        ge=1,
        description="Updated participant limit",
    )
    status: EventStatus | None = Field(
        default=None,
        description="Updated event status",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated Study Session",
                "participant_limit": 30,
            }
        }
    }


class EventResponse(BaseModel):
    """Schema for event response.

    Used when returning event information in lists or details.

    Attributes:
        id: Event unique identifier.
        community_id: Community hosting this event.
        creator_id: User who created the event.
        title: Event title.
        description: Event description.
        type: Event type.
        location: Event location or meeting link.
        start_time: Event start time.
        end_time: Event end time.
        participant_limit: Maximum participants.
        registered_count: Number of registered participants.
        status: Event status.
        created_at: When the event was created.
        updated_at: When the event was last updated.
    """

    id: UUID
    community_id: UUID
    creator_id: UUID
    title: str
    description: str
    type: EventType
    location: str | None
    start_time: datetime
    end_time: datetime
    participant_limit: int | None
    registered_count: int = Field(
        default=0,
        description="Number of registered participants",
    )
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "community_id": "123e4567-e89b-12d3-a456-426614174001",
                "creator_id": "123e4567-e89b-12d3-a456-426614174002",
                "title": "Weekly Study Session",
                "description": "Join us for our weekly calculus study session.",
                "type": "online",
                "location": "https://zoom.us/j/123456789",
                "start_time": "2025-12-01T14:00:00Z",
                "end_time": "2025-12-01T16:00:00Z",
                "participant_limit": 20,
                "registered_count": 15,
                "status": "published",
                "created_at": "2025-11-01T10:00:00Z",
                "updated_at": "2025-11-01T10:00:00Z",
            }
        },
    }


class EventDetailResponse(EventResponse):
    """Extended event response with additional details.

    Includes same fields as EventResponse. Can be extended with
    creator info, community info, or participant lists if needed.
    """

    pass


class EventRegistrationResponse(BaseModel):
    """Schema for event registration response.

    Attributes:
        event_id: Event identifier.
        user_id: User identifier.
        status: Registration status (registered, waitlisted, attended, no_show).
        registered_at: When the user registered.
    """

    event_id: UUID
    user_id: UUID
    status: str = Field(
        ...,
        description="Registration status",
    )
    registered_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "status": "registered",
                "registered_at": "2025-11-05T12:00:00Z",
            }
        },
    }


class EventParticipantResponse(BaseModel):
    """Schema for event participant response.

    Attributes:
        user_id: Participant user ID.
        email: Participant email.
        full_name: Participant full name.
        status: Registration status.
        registered_at: When they registered.
    """

    user_id: UUID
    email: str
    full_name: str
    status: str
    registered_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "email": "john.doe@stanford.edu",
                "full_name": "John Doe",
                "status": "registered",
                "registered_at": "2025-11-05T12:00:00Z",
            }
        }
    }
