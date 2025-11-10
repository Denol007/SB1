"""Unit tests for post schemas.

Tests for:
- AttachmentSchema
- PostCreate
- PostUpdate
- PostResponse
- PostDetailResponse
- ReactionCount
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.post import (
    AttachmentSchema,
    PostCreate,
    PostDetailResponse,
    PostResponse,
    PostUpdate,
    ReactionCount,
)
from app.domain.enums.reaction_type import ReactionType


class TestAttachmentSchema:
    """Tests for AttachmentSchema."""

    def test_valid_attachment(self) -> None:
        """Test valid attachment with all fields."""
        attachment = AttachmentSchema(
            type="image",
            url="https://example.com/image.jpg",
            filename="image.jpg",
            size=1024000,
            mime_type="image/jpeg",
        )

        assert attachment.type == "image"
        assert attachment.url == "https://example.com/image.jpg"
        assert attachment.filename == "image.jpg"
        assert attachment.size == 1024000
        assert attachment.mime_type == "image/jpeg"

    def test_attachment_without_optional_fields(self) -> None:
        """Test attachment without optional size and mime_type."""
        attachment = AttachmentSchema(
            type="file",
            url="https://example.com/document.pdf",
            filename="document.pdf",
        )

        assert attachment.type == "file"
        assert attachment.size is None
        assert attachment.mime_type is None

    def test_attachment_with_zero_size(self) -> None:
        """Test attachment with zero size (empty file)."""
        attachment = AttachmentSchema(
            type="text",
            url="https://example.com/empty.txt",
            filename="empty.txt",
            size=0,
        )

        assert attachment.size == 0

    def test_attachment_negative_size_fails(self) -> None:
        """Test that negative size fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            AttachmentSchema(
                type="image",
                url="https://example.com/image.jpg",
                filename="image.jpg",
                size=-1,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "greater_than_equal" for err in errors)

    def test_attachment_empty_type_fails(self) -> None:
        """Test that empty type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            AttachmentSchema(
                type="",
                url="https://example.com/file",
                filename="file",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_attachment_type_too_long_fails(self) -> None:
        """Test that type exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            AttachmentSchema(
                type="x" * 51,  # Max is 50
                url="https://example.com/file",
                filename="file",
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)


class TestPostCreate:
    """Tests for PostCreate schema."""

    def test_valid_post_create(self) -> None:
        """Test valid post creation with content only."""
        post_data = PostCreate(
            content="Just finished my CS221 assignment!",
        )

        assert post_data.content == "Just finished my CS221 assignment!"
        assert post_data.attachments is None

    def test_post_create_with_attachments(self) -> None:
        """Test post creation with attachments."""
        post_data = PostCreate(
            content="Check out my project!",
            attachments=[
                AttachmentSchema(
                    type="image",
                    url="https://example.com/screenshot.png",
                    filename="screenshot.png",
                    size=512000,
                    mime_type="image/png",
                )
            ],
        )

        assert post_data.content == "Check out my project!"
        assert post_data.attachments is not None
        assert len(post_data.attachments) == 1
        assert post_data.attachments[0].filename == "screenshot.png"

    def test_post_create_with_multiple_attachments(self) -> None:
        """Test post creation with multiple attachments."""
        post_data = PostCreate(
            content="My study materials",
            attachments=[
                AttachmentSchema(
                    type="image",
                    url="https://example.com/image1.jpg",
                    filename="image1.jpg",
                ),
                AttachmentSchema(
                    type="image",
                    url="https://example.com/image2.jpg",
                    filename="image2.jpg",
                ),
                AttachmentSchema(
                    type="pdf",
                    url="https://example.com/notes.pdf",
                    filename="notes.pdf",
                ),
            ],
        )

        assert len(post_data.attachments) == 3

    def test_empty_content_fails(self) -> None:
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            PostCreate(content="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_content_too_long_fails(self) -> None:
        """Test that content exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            PostCreate(content="x" * 10001)  # Max is 10000

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)

    def test_too_many_attachments_fails(self) -> None:
        """Test that more than 10 attachments fails validation."""
        attachments = [
            AttachmentSchema(
                type="image",
                url=f"https://example.com/image{i}.jpg",
                filename=f"image{i}.jpg",
            )
            for i in range(11)  # Max is 10
        ]

        with pytest.raises(ValidationError) as exc_info:
            PostCreate(
                content="Too many attachments",
                attachments=attachments,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "too_long" for err in errors)

    def test_max_length_content_succeeds(self) -> None:
        """Test that content at max length succeeds."""
        post_data = PostCreate(content="x" * 10000)  # Exactly at max
        assert len(post_data.content) == 10000


class TestPostUpdate:
    """Tests for PostUpdate schema."""

    def test_update_content_only(self) -> None:
        """Test updating content only."""
        update_data = PostUpdate(content="Updated content")

        assert update_data.content == "Updated content"
        assert update_data.attachments is None

    def test_update_attachments_only(self) -> None:
        """Test updating attachments only."""
        update_data = PostUpdate(
            attachments=[
                AttachmentSchema(
                    type="image",
                    url="https://example.com/new-image.jpg",
                    filename="new-image.jpg",
                )
            ]
        )

        assert update_data.content is None
        assert update_data.attachments is not None
        assert len(update_data.attachments) == 1

    def test_update_both_fields(self) -> None:
        """Test updating both content and attachments."""
        update_data = PostUpdate(
            content="Updated content",
            attachments=[
                AttachmentSchema(
                    type="image",
                    url="https://example.com/updated.jpg",
                    filename="updated.jpg",
                )
            ],
        )

        assert update_data.content == "Updated content"
        assert len(update_data.attachments) == 1

    def test_update_with_no_fields(self) -> None:
        """Test update with no fields (all None)."""
        update_data = PostUpdate()

        assert update_data.content is None
        assert update_data.attachments is None

    def test_update_empty_content_fails(self) -> None:
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            PostUpdate(content="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_update_content_too_long_fails(self) -> None:
        """Test that content exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            PostUpdate(content="x" * 10001)

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)

    def test_update_clear_attachments(self) -> None:
        """Test updating to clear attachments (empty list)."""
        update_data = PostUpdate(attachments=[])

        assert update_data.attachments == []


class TestPostResponse:
    """Tests for PostResponse schema."""

    def test_valid_post_response(self) -> None:
        """Test valid post response with all required fields."""
        post_id = uuid4()
        author_id = uuid4()
        community_id = uuid4()
        now = datetime.now(UTC)

        response = PostResponse(
            id=post_id,
            author_id=author_id,
            community_id=community_id,
            content="Test post content",
            attachments=None,
            is_pinned=False,
            edited_at=None,
            created_at=now,
            updated_at=now,
        )

        assert response.id == post_id
        assert response.author_id == author_id
        assert response.community_id == community_id
        assert response.content == "Test post content"
        assert response.attachments is None
        assert response.is_pinned is False
        assert response.edited_at is None
        assert response.created_at == now
        assert response.updated_at == now

    def test_post_response_with_attachments(self) -> None:
        """Test post response with attachments."""
        response = PostResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Post with attachments",
            attachments=[
                {
                    "type": "image",
                    "url": "https://example.com/image.jpg",
                    "filename": "image.jpg",
                }
            ],
            is_pinned=False,
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.attachments is not None
        assert len(response.attachments) == 1
        assert response.attachments[0]["filename"] == "image.jpg"

    def test_post_response_pinned(self) -> None:
        """Test post response for pinned post."""
        response = PostResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Pinned announcement",
            attachments=None,
            is_pinned=True,
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.is_pinned is True

    def test_post_response_edited(self) -> None:
        """Test post response for edited post."""
        now = datetime.now(UTC)
        edited_time = now.replace(hour=now.hour + 1)

        response = PostResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Edited post",
            attachments=None,
            is_pinned=False,
            edited_at=edited_time,
            created_at=now,
            updated_at=edited_time,
        )

        assert response.edited_at == edited_time
        assert response.edited_at > response.created_at


class TestReactionCount:
    """Tests for ReactionCount schema."""

    def test_valid_reaction_count(self) -> None:
        """Test valid reaction count."""
        reaction_count = ReactionCount(
            reaction_type=ReactionType.LIKE,
            count=42,
        )

        assert reaction_count.reaction_type == ReactionType.LIKE
        assert reaction_count.count == 42

    def test_reaction_count_zero(self) -> None:
        """Test reaction count with zero count."""
        reaction_count = ReactionCount(
            reaction_type=ReactionType.LOVE,
            count=0,
        )

        assert reaction_count.count == 0

    def test_reaction_count_all_types(self) -> None:
        """Test reaction counts for all reaction types."""
        for reaction_type in ReactionType:
            reaction_count = ReactionCount(
                reaction_type=reaction_type,
                count=10,
            )
            assert reaction_count.reaction_type == reaction_type

    def test_negative_count_fails(self) -> None:
        """Test that negative count fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            ReactionCount(
                reaction_type=ReactionType.LIKE,
                count=-1,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "greater_than_equal" for err in errors)


class TestPostDetailResponse:
    """Tests for PostDetailResponse schema."""

    def test_valid_post_detail_response(self) -> None:
        """Test valid detailed post response with all fields."""
        post_id = uuid4()
        author_id = uuid4()
        community_id = uuid4()
        now = datetime.now(UTC)

        response = PostDetailResponse(
            id=post_id,
            author_id=author_id,
            community_id=community_id,
            content="Detailed post",
            attachments=None,
            is_pinned=False,
            edited_at=None,
            created_at=now,
            updated_at=now,
            author_name="John Doe",
            author_avatar_url="https://example.com/avatar.jpg",
            community_name="Stanford CS",
            reaction_counts=[
                ReactionCount(reaction_type=ReactionType.LIKE, count=42),
                ReactionCount(reaction_type=ReactionType.LOVE, count=15),
            ],
            comment_count=23,
            user_reaction=ReactionType.LIKE,
        )

        assert response.author_name == "John Doe"
        assert response.author_avatar_url == "https://example.com/avatar.jpg"
        assert response.community_name == "Stanford CS"
        assert len(response.reaction_counts) == 2
        assert response.comment_count == 23
        assert response.user_reaction == ReactionType.LIKE

    def test_post_detail_with_no_reactions(self) -> None:
        """Test detailed post with no reactions."""
        response = PostDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Post with no reactions",
            attachments=None,
            is_pinned=False,
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reaction_counts=[],
            comment_count=0,
        )

        assert response.reaction_counts == []
        assert response.comment_count == 0
        assert response.user_reaction is None

    def test_post_detail_with_multiple_reaction_types(self) -> None:
        """Test detailed post with all reaction types."""
        response = PostDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Popular post",
            attachments=None,
            is_pinned=False,
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reaction_counts=[
                ReactionCount(reaction_type=ReactionType.LIKE, count=100),
                ReactionCount(reaction_type=ReactionType.LOVE, count=50),
                ReactionCount(reaction_type=ReactionType.CELEBRATE, count=30),
                ReactionCount(reaction_type=ReactionType.SUPPORT, count=20),
            ],
            comment_count=150,
        )

        assert len(response.reaction_counts) == 4
        total_reactions = sum(rc.count for rc in response.reaction_counts)
        assert total_reactions == 200

    def test_post_detail_negative_comment_count_fails(self) -> None:
        """Test that negative comment count fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            PostDetailResponse(
                id=uuid4(),
                author_id=uuid4(),
                community_id=uuid4(),
                content="Test post",
                attachments=None,
                is_pinned=False,
                edited_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                comment_count=-1,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "greater_than_equal" for err in errors)

    def test_post_detail_optional_author_fields(self) -> None:
        """Test detailed post with optional author fields as None."""
        response = PostDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            community_id=uuid4(),
            content="Test post",
            attachments=None,
            is_pinned=False,
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            author_name=None,
            author_avatar_url=None,
            community_name=None,
        )

        assert response.author_name is None
        assert response.author_avatar_url is None
        assert response.community_name is None
