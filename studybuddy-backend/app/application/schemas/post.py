"""Post schemas (DTOs) for request/response validation.

Pydantic models for:
- Post creation and updates
- Post list and detail responses
- Reaction counts and comment metadata
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums.reaction_type import ReactionType


class AttachmentSchema(BaseModel):
    """Schema for post attachments.

    Represents a single attachment (image, file, etc.) in a post.

    Attributes:
        type: Type of attachment (image, file, video, etc.).
        url: URL to the attachment.
        filename: Original filename.
        size: File size in bytes (optional).
        mime_type: MIME type of the file (optional).

    Example:
        >>> attachment = AttachmentSchema(
        ...     type="image",
        ...     url="https://cdn.example.com/images/photo.jpg",
        ...     filename="photo.jpg",
        ...     size=1024000,
        ...     mime_type="image/jpeg"
        ... )
    """

    type: str = Field(
        ...,
        description="Type of attachment (image, file, video, etc.)",
        min_length=1,
        max_length=50,
    )
    url: str = Field(
        ...,
        description="URL to the attachment",
        max_length=2000,
    )
    filename: str = Field(
        ...,
        description="Original filename",
        max_length=255,
    )
    size: int | None = Field(
        default=None,
        description="File size in bytes",
        ge=0,
    )
    mime_type: str | None = Field(
        default=None,
        description="MIME type of the file",
        max_length=100,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "image",
                "url": "https://cdn.example.com/images/study-notes.jpg",
                "filename": "study-notes.jpg",
                "size": 1024000,
                "mime_type": "image/jpeg",
            }
        }
    }


class PostCreate(BaseModel):
    """Schema for creating a new post.

    Used when creating a post in a community.
    The community_id is typically provided in the URL path.

    Attributes:
        content: Post text content (1-10000 characters).
        attachments: Optional list of attachments (images, files, etc.).

    Example:
        >>> post = PostCreate(
        ...     content="Just finished my CS221 assignment! Anyone else working on Problem Set 3?",
        ...     attachments=[
        ...         {
        ...             "type": "image",
        ...             "url": "https://cdn.example.com/images/assignment.jpg",
        ...             "filename": "assignment.jpg"
        ...         }
        ...     ]
        ... )
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Post text content",
    )
    attachments: list[AttachmentSchema] | None = Field(
        default=None,
        description="Optional list of attachments",
        max_length=10,  # Limit to 10 attachments per post
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Just finished my CS221 assignment! Anyone else working on Problem Set 3?",
                "attachments": [
                    {
                        "type": "image",
                        "url": "https://cdn.example.com/images/assignment.jpg",
                        "filename": "assignment.jpg",
                        "size": 512000,
                        "mime_type": "image/jpeg",
                    }
                ],
            }
        }
    }


class PostUpdate(BaseModel):
    """Schema for updating an existing post.

    All fields are optional. Only provided fields will be updated.
    Only the post author or community moderators can update posts.

    Attributes:
        content: Updated post text content (1-10000 characters).
        attachments: Updated list of attachments (replaces existing).

    Example:
        >>> update = PostUpdate(
        ...     content="Updated: Just finished my CS221 assignment! Problem Set 3 was challenging."
        ... )
    """

    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=10000,
        description="Updated post text content",
    )
    attachments: list[AttachmentSchema] | None = Field(
        default=None,
        description="Updated list of attachments (replaces existing)",
        max_length=10,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Updated: Just finished my CS221 assignment! Problem Set 3 was really challenging but rewarding.",
            }
        }
    }


class PostResponse(BaseModel):
    """Schema for basic post response.

    Standard post information returned by list endpoints.

    Attributes:
        id: Post's unique identifier.
        author_id: UUID of the user who created the post.
        community_id: UUID of the community this post belongs to.
        content: Post text content.
        attachments: Optional list of attachments.
        is_pinned: Whether the post is pinned to the top of the feed.
        edited_at: Timestamp when post was last edited (None if never edited).
        created_at: Timestamp when post was created.
        updated_at: Timestamp when post was last updated.

    Example:
        >>> response = PostResponse(
        ...     id=uuid4(),
        ...     author_id=user_id,
        ...     community_id=community_id,
        ...     content="Great study session!",
        ...     attachments=None,
        ...     is_pinned=False,
        ...     edited_at=None,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """

    id: UUID = Field(..., description="Post unique identifier")
    author_id: UUID = Field(..., description="Author's user ID")
    community_id: UUID = Field(..., description="Community ID")
    content: str = Field(..., description="Post text content")
    attachments: list[dict[str, Any]] | None = Field(
        None, description="Optional list of attachments"
    )
    is_pinned: bool = Field(False, description="Whether post is pinned")
    edited_at: datetime | None = Field(None, description="Last edit timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,  # Enable ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "author_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "community_id": "456e7890-a12b-34c5-d678-901234567890",
                "content": "Just finished my CS221 assignment! Anyone else working on Problem Set 3?",
                "attachments": [
                    {
                        "type": "image",
                        "url": "https://cdn.example.com/images/assignment.jpg",
                        "filename": "assignment.jpg",
                        "size": 512000,
                        "mime_type": "image/jpeg",
                    }
                ],
                "is_pinned": False,
                "edited_at": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class ReactionCount(BaseModel):
    """Schema for reaction count by type.

    Represents the count of a specific reaction type on a post.

    Attributes:
        reaction_type: Type of reaction (like, love, celebrate, support).
        count: Number of reactions of this type.

    Example:
        >>> reaction_count = ReactionCount(
        ...     reaction_type=ReactionType.LIKE,
        ...     count=42
        ... )
    """

    reaction_type: ReactionType = Field(..., description="Type of reaction")
    count: int = Field(..., ge=0, description="Number of reactions")

    model_config = {
        "json_schema_extra": {
            "example": {
                "reaction_type": "like",
                "count": 42,
            }
        }
    }


class PostDetailResponse(PostResponse):
    """Schema for detailed post response.

    Extended post information with reaction counts and comment metadata.
    Used for single post detail endpoints.

    Attributes:
        author_name: Name of the post author (set by service layer).
        author_avatar_url: Avatar URL of the post author (set by service layer).
        community_name: Name of the community (set by service layer).
        reaction_counts: List of reaction counts by type.
        comment_count: Total number of comments on the post.
        user_reaction: Current user's reaction to the post (set by service layer).

    Example:
        >>> response = PostDetailResponse(
        ...     id=uuid4(),
        ...     author_id=user_id,
        ...     community_id=community_id,
        ...     content="Great study session!",
        ...     attachments=None,
        ...     is_pinned=False,
        ...     edited_at=None,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ...     author_name="John Doe",
        ...     author_avatar_url="https://example.com/avatar.jpg",
        ...     community_name="Stanford CS",
        ...     reaction_counts=[
        ...         ReactionCount(reaction_type=ReactionType.LIKE, count=42),
        ...         ReactionCount(reaction_type=ReactionType.LOVE, count=15)
        ...     ],
        ...     comment_count=8,
        ...     user_reaction=ReactionType.LIKE
        ... )
    """

    author_name: str | None = Field(
        default=None,
        description="Name of the post author",
    )
    author_avatar_url: str | None = Field(
        default=None,
        description="Avatar URL of the post author",
    )
    community_name: str | None = Field(
        default=None,
        description="Name of the community",
    )
    reaction_counts: list[ReactionCount] = Field(
        default_factory=list,
        description="List of reaction counts by type",
    )
    comment_count: int = Field(
        default=0,
        ge=0,
        description="Total number of comments on the post",
    )
    user_reaction: ReactionType | None = Field(
        default=None,
        description="Current user's reaction to the post (if any)",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "author_id": "987fcdeb-51a2-43f7-9876-543210987654",
                "community_id": "456e7890-a12b-34c5-d678-901234567890",
                "content": "Just finished my CS221 assignment! Anyone else working on Problem Set 3?",
                "attachments": None,
                "is_pinned": False,
                "edited_at": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "author_name": "John Doe",
                "author_avatar_url": "https://example.com/avatars/johndoe.jpg",
                "community_name": "Stanford Computer Science",
                "reaction_counts": [
                    {"reaction_type": "like", "count": 42},
                    {"reaction_type": "love", "count": 15},
                    {"reaction_type": "celebrate", "count": 8},
                ],
                "comment_count": 23,
                "user_reaction": "like",
            }
        },
    }
