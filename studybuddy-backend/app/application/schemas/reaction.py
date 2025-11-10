"""Reaction schemas (DTOs) for request/response validation.

Pydantic models for:
- Reaction creation
- Reaction responses
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums.reaction_type import ReactionType


class ReactionCreate(BaseModel):
    """Schema for creating a reaction.

    Used when a user adds a reaction to a post.

    Attributes:
        reaction_type: Type of reaction (like, love, celebrate, support).

    Example:
        >>> reaction_data = ReactionCreate(
        ...     reaction_type=ReactionType.LIKE
        ... )
    """

    reaction_type: ReactionType = Field(
        ...,
        description="Type of reaction (like, love, celebrate, support)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reaction_type": "like",
            }
        }
    }


class ReactionResponse(BaseModel):
    """Schema for reaction response.

    Returned when getting reaction details.

    Attributes:
        id: Unique reaction identifier.
        user_id: UUID of the user who reacted.
        post_id: UUID of the post being reacted to.
        reaction_type: Type of reaction.
        created_at: Timestamp when reaction was created.
        updated_at: Timestamp when reaction was last updated.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, UTC
        >>> reaction = ReactionResponse(
        ...     id=uuid4(),
        ...     user_id=uuid4(),
        ...     post_id=uuid4(),
        ...     reaction_type=ReactionType.CELEBRATE,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC)
        ... )
    """

    id: UUID = Field(
        ...,
        description="Unique reaction identifier",
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who reacted",
    )
    post_id: UUID = Field(
        ...,
        description="UUID of the post being reacted to",
    )
    reaction_type: ReactionType = Field(
        ...,
        description="Type of reaction",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when reaction was created",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when reaction was last updated",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "post_id": "456e7890-a12b-34c5-d678-901234567890",
                "reaction_type": "celebrate",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class ReactionDetailResponse(ReactionResponse):
    """Schema for detailed reaction response.

    Extends ReactionResponse with additional user information.

    Attributes:
        user_name: Name of the user who reacted.
        user_avatar_url: Avatar URL of the user.

    Example:
        >>> reaction_detail = ReactionDetailResponse(
        ...     id=uuid4(),
        ...     user_id=uuid4(),
        ...     post_id=uuid4(),
        ...     reaction_type=ReactionType.LOVE,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC),
        ...     user_name="Jane Smith",
        ...     user_avatar_url="https://example.com/avatars/jane.jpg"
        ... )
    """

    user_name: str | None = Field(
        default=None,
        description="Name of the user who reacted",
    )
    user_avatar_url: str | None = Field(
        default=None,
        description="Avatar URL of the user",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "post_id": "456e7890-a12b-34c5-d678-901234567890",
                "reaction_type": "love",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "user_name": "Jane Smith",
                "user_avatar_url": "https://example.com/avatars/jane.jpg",
            }
        },
    }
