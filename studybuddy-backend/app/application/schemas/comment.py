"""Comment schemas (DTOs) for request/response validation.

Pydantic models for:
- Comment creation and updates
- Comment responses with threading support
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """Schema for creating a new comment.

    Used when creating a comment on a post or replying to another comment.

    Attributes:
        content: Comment text content (1-5000 characters).
        parent_id: Optional UUID of parent comment for threaded replies.

    Example:
        >>> comment = CommentCreate(
        ...     content="Great insight! I totally agree with your analysis."
        ... )

        >>> reply = CommentCreate(
        ...     content="Thanks! Glad you found it helpful.",
        ...     parent_id=UUID("123e4567-e89b-12d3-a456-426614174000")
        ... )
    """

    content: str = Field(
        ...,
        description="Comment text content",
        min_length=1,
        max_length=5000,
    )
    parent_id: UUID | None = Field(
        default=None,
        description="UUID of parent comment for threaded replies",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Great insight! I totally agree with your analysis.",
                "parent_id": None,
            }
        }
    }


class CommentUpdate(BaseModel):
    """Schema for updating a comment.

    Only the content can be updated. Optional field allows partial updates.

    Attributes:
        content: Updated comment text content (1-5000 characters).

    Example:
        >>> update = CommentUpdate(
        ...     content="Updated: Great insight! I totally agree with your detailed analysis."
        ... )
    """

    content: str | None = Field(
        default=None,
        description="Updated comment text content",
        min_length=1,
        max_length=5000,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Updated: Great insight! I totally agree with your detailed analysis.",
            }
        }
    }


class CommentResponse(BaseModel):
    """Schema for comment response.

    Returned when getting comment details.

    Attributes:
        id: Unique comment identifier.
        author_id: UUID of the user who created the comment.
        post_id: UUID of the post this comment belongs to.
        parent_id: Optional UUID of parent comment for replies.
        content: Comment text content.
        edited_at: Timestamp when comment was last edited (None if never edited).
        created_at: Timestamp when comment was created.
        updated_at: Timestamp when comment was last updated.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, UTC
        >>> comment = CommentResponse(
        ...     id=uuid4(),
        ...     author_id=uuid4(),
        ...     post_id=uuid4(),
        ...     parent_id=None,
        ...     content="Great post!",
        ...     edited_at=None,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC)
        ... )
    """

    id: UUID = Field(
        ...,
        description="Unique comment identifier",
    )
    author_id: UUID = Field(
        ...,
        description="UUID of the user who created the comment",
    )
    post_id: UUID = Field(
        ...,
        description="UUID of the post this comment belongs to",
    )
    parent_id: UUID | None = Field(
        default=None,
        description="UUID of parent comment for replies",
    )
    content: str = Field(
        ...,
        description="Comment text content",
    )
    edited_at: datetime | None = Field(
        default=None,
        description="Timestamp when comment was last edited",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when comment was created",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when comment was last updated",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "author_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "post_id": "456e7890-a12b-34c5-d678-901234567890",
                "parent_id": None,
                "content": "Great post! Really helpful insights.",
                "edited_at": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class CommentDetailResponse(CommentResponse):
    """Schema for detailed comment response.

    Extends CommentResponse with additional author information.

    Attributes:
        author_name: Name of the comment author.
        author_avatar_url: Avatar URL of the comment author.
        reply_count: Number of direct replies to this comment.

    Example:
        >>> comment_detail = CommentDetailResponse(
        ...     id=uuid4(),
        ...     author_id=uuid4(),
        ...     post_id=uuid4(),
        ...     parent_id=None,
        ...     content="Great post!",
        ...     edited_at=None,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC),
        ...     author_name="John Doe",
        ...     author_avatar_url="https://example.com/avatars/johndoe.jpg",
        ...     reply_count=5
        ... )
    """

    author_name: str | None = Field(
        default=None,
        description="Name of the comment author",
    )
    author_avatar_url: str | None = Field(
        default=None,
        description="Avatar URL of the comment author",
    )
    reply_count: int = Field(
        default=0,
        ge=0,
        description="Number of direct replies to this comment",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "author_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "post_id": "456e7890-a12b-34c5-d678-901234567890",
                "parent_id": None,
                "content": "Great post! Really helpful insights on the algorithm.",
                "edited_at": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "author_name": "John Doe",
                "author_avatar_url": "https://example.com/avatars/johndoe.jpg",
                "reply_count": 5,
            }
        },
    }
