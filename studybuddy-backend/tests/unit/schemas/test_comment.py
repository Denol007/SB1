"""Unit tests for comment schemas.

Tests for:
- CommentCreate
- CommentUpdate
- CommentResponse
- CommentDetailResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.comment import (
    CommentCreate,
    CommentDetailResponse,
    CommentResponse,
    CommentUpdate,
)


class TestCommentCreate:
    """Tests for CommentCreate schema."""

    def test_valid_comment_create(self) -> None:
        """Test creating a valid comment."""
        comment_data = CommentCreate(content="Great post! Really helpful insights.")

        assert comment_data.content == "Great post! Really helpful insights."
        assert comment_data.parent_id is None

    def test_comment_create_with_parent_id(self) -> None:
        """Test creating a reply comment with parent_id."""
        parent_id = uuid4()
        comment_data = CommentCreate(content="Thanks for sharing!", parent_id=parent_id)

        assert comment_data.content == "Thanks for sharing!"
        assert comment_data.parent_id == parent_id

    def test_comment_create_min_length(self) -> None:
        """Test comment with minimum length (1 character)."""
        comment_data = CommentCreate(content="x")

        assert len(comment_data.content) == 1

    def test_comment_create_max_length(self) -> None:
        """Test comment at maximum length (5000 characters)."""
        comment_data = CommentCreate(content="x" * 5000)

        assert len(comment_data.content) == 5000

    def test_empty_content_fails(self) -> None:
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate(content="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_content_too_long_fails(self) -> None:
        """Test that content exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate(content="x" * 5001)  # Max is 5000

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)

    def test_missing_content_fails(self) -> None:
        """Test that missing content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate()  # type: ignore

        errors = exc_info.value.errors()
        assert any(err["type"] == "missing" for err in errors)

    def test_content_with_newlines(self) -> None:
        """Test comment content with newlines."""
        content = "Line 1\nLine 2\nLine 3"
        comment_data = CommentCreate(content=content)

        assert comment_data.content == content

    def test_content_with_special_characters(self) -> None:
        """Test comment with special characters."""
        content = "Hello! 👍 This is great 🎉 @user #topic"
        comment_data = CommentCreate(content=content)

        assert comment_data.content == content


class TestCommentUpdate:
    """Tests for CommentUpdate schema."""

    def test_update_content(self) -> None:
        """Test updating comment content."""
        update_data = CommentUpdate(content="Updated content here")

        assert update_data.content == "Updated content here"

    def test_update_with_no_content(self) -> None:
        """Test update with no content (None)."""
        update_data = CommentUpdate()

        assert update_data.content is None

    def test_update_content_min_length(self) -> None:
        """Test update with minimum length content."""
        update_data = CommentUpdate(content="x")

        assert len(update_data.content) == 1

    def test_update_content_max_length(self) -> None:
        """Test update at maximum length."""
        update_data = CommentUpdate(content="x" * 5000)

        assert len(update_data.content) == 5000

    def test_update_empty_content_fails(self) -> None:
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommentUpdate(content="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_update_content_too_long_fails(self) -> None:
        """Test that content exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommentUpdate(content="x" * 5001)

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)


class TestCommentResponse:
    """Tests for CommentResponse schema."""

    def test_valid_comment_response(self) -> None:
        """Test valid comment response with all fields."""
        comment_id = uuid4()
        author_id = uuid4()
        post_id = uuid4()
        now = datetime.now(UTC)

        response = CommentResponse(
            id=comment_id,
            author_id=author_id,
            post_id=post_id,
            parent_id=None,
            content="Great post!",
            edited_at=None,
            created_at=now,
            updated_at=now,
        )

        assert response.id == comment_id
        assert response.author_id == author_id
        assert response.post_id == post_id
        assert response.parent_id is None
        assert response.content == "Great post!"
        assert response.edited_at is None
        assert response.created_at == now
        assert response.updated_at == now

    def test_comment_response_with_parent_id(self) -> None:
        """Test comment response for a reply."""
        parent_id = uuid4()
        response = CommentResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=parent_id,
            content="Reply to parent comment",
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.parent_id == parent_id

    def test_comment_response_edited(self) -> None:
        """Test comment response for edited comment."""
        now = datetime.now(UTC)
        edited_time = now.replace(hour=(now.hour + 1) % 24)

        response = CommentResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=None,
            content="Edited comment",
            edited_at=edited_time,
            created_at=now,
            updated_at=edited_time,
        )

        assert response.edited_at == edited_time
        assert response.edited_at >= response.created_at

    def test_comment_response_missing_required_field_fails(self) -> None:
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommentResponse(
                id=uuid4(),
                author_id=uuid4(),
                # Missing post_id, content, timestamps
                content="Test",
            )  # type: ignore

        errors = exc_info.value.errors()
        assert any(err["type"] == "missing" for err in errors)

    def test_comment_response_from_attributes(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        config = CommentResponse.model_config
        assert config.get("from_attributes") is True


class TestCommentDetailResponse:
    """Tests for CommentDetailResponse schema."""

    def test_valid_comment_detail_response(self) -> None:
        """Test valid detailed comment response with all fields."""
        comment_id = uuid4()
        author_id = uuid4()
        post_id = uuid4()
        now = datetime.now(UTC)

        response = CommentDetailResponse(
            id=comment_id,
            author_id=author_id,
            post_id=post_id,
            parent_id=None,
            content="Great post with detailed analysis!",
            edited_at=None,
            created_at=now,
            updated_at=now,
            author_name="John Doe",
            author_avatar_url="https://example.com/avatars/johndoe.jpg",
            reply_count=5,
        )

        assert response.author_name == "John Doe"
        assert response.author_avatar_url == "https://example.com/avatars/johndoe.jpg"
        assert response.reply_count == 5

    def test_comment_detail_without_author_info(self) -> None:
        """Test detailed comment without optional author info."""
        response = CommentDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=None,
            content="Comment without author info",
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.author_name is None
        assert response.author_avatar_url is None
        assert response.reply_count == 0

    def test_comment_detail_with_author_name_only(self) -> None:
        """Test detailed comment with only author name."""
        response = CommentDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=None,
            content="Comment",
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            author_name="Jane Smith",
        )

        assert response.author_name == "Jane Smith"
        assert response.author_avatar_url is None

    def test_comment_detail_with_replies(self) -> None:
        """Test detailed comment with reply count."""
        response = CommentDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=None,
            content="Popular comment",
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reply_count=42,
        )

        assert response.reply_count == 42

    def test_comment_detail_negative_reply_count_fails(self) -> None:
        """Test that negative reply count fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommentDetailResponse(
                id=uuid4(),
                author_id=uuid4(),
                post_id=uuid4(),
                parent_id=None,
                content="Test",
                edited_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                reply_count=-1,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "greater_than_equal" for err in errors)

    def test_comment_detail_threaded_reply(self) -> None:
        """Test detailed comment for a threaded reply."""
        parent_id = uuid4()
        response = CommentDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=parent_id,
            content="Reply in thread",
            edited_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            author_name="Thread User",
            reply_count=2,
        )

        assert response.parent_id == parent_id
        assert response.reply_count == 2

    def test_comment_detail_inherits_from_comment_response(self) -> None:
        """Test that CommentDetailResponse inherits all CommentResponse fields."""
        now = datetime.now(UTC)
        response = CommentDetailResponse(
            id=uuid4(),
            author_id=uuid4(),
            post_id=uuid4(),
            parent_id=None,
            content="Test comment",
            edited_at=None,
            created_at=now,
            updated_at=now,
            author_name="Test User",
        )

        # Verify all base fields are present
        assert hasattr(response, "id")
        assert hasattr(response, "author_id")
        assert hasattr(response, "post_id")
        assert hasattr(response, "parent_id")
        assert hasattr(response, "content")
        assert hasattr(response, "edited_at")
        assert hasattr(response, "created_at")
        assert hasattr(response, "updated_at")

        # Verify extended fields are present
        assert hasattr(response, "author_name")
        assert hasattr(response, "author_avatar_url")
        assert hasattr(response, "reply_count")

    def test_comment_detail_from_attributes(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        config = CommentDetailResponse.model_config
        assert config.get("from_attributes") is True
