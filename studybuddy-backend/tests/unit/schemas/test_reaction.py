"""Unit tests for reaction schemas.

Tests for:
- ReactionCreate
- ReactionResponse
- ReactionDetailResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.reaction import (
    ReactionCreate,
    ReactionDetailResponse,
    ReactionResponse,
)
from app.domain.enums.reaction_type import ReactionType


class TestReactionCreate:
    """Tests for ReactionCreate schema."""

    def test_valid_reaction_create_like(self) -> None:
        """Test creating a like reaction."""
        reaction_data = ReactionCreate(reaction_type=ReactionType.LIKE)

        assert reaction_data.reaction_type == ReactionType.LIKE

    def test_valid_reaction_create_love(self) -> None:
        """Test creating a love reaction."""
        reaction_data = ReactionCreate(reaction_type=ReactionType.LOVE)

        assert reaction_data.reaction_type == ReactionType.LOVE

    def test_valid_reaction_create_celebrate(self) -> None:
        """Test creating a celebrate reaction."""
        reaction_data = ReactionCreate(reaction_type=ReactionType.CELEBRATE)

        assert reaction_data.reaction_type == ReactionType.CELEBRATE

    def test_valid_reaction_create_support(self) -> None:
        """Test creating a support reaction."""
        reaction_data = ReactionCreate(reaction_type=ReactionType.SUPPORT)

        assert reaction_data.reaction_type == ReactionType.SUPPORT

    def test_reaction_create_with_string_value(self) -> None:
        """Test creating reaction with string value."""
        reaction_data = ReactionCreate(reaction_type="like")

        assert reaction_data.reaction_type == ReactionType.LIKE

    def test_reaction_create_all_types(self) -> None:
        """Test creating reactions for all reaction types."""
        for reaction_type in ReactionType:
            reaction_data = ReactionCreate(reaction_type=reaction_type)
            assert reaction_data.reaction_type == reaction_type

    def test_invalid_reaction_type_fails(self) -> None:
        """Test that invalid reaction type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            ReactionCreate(reaction_type="invalid_type")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("reaction_type" in str(err) for err in errors)

    def test_missing_reaction_type_fails(self) -> None:
        """Test that missing reaction type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            ReactionCreate()  # type: ignore

        errors = exc_info.value.errors()
        assert any(err["type"] == "missing" for err in errors)


class TestReactionResponse:
    """Tests for ReactionResponse schema."""

    def test_valid_reaction_response(self) -> None:
        """Test valid reaction response with all fields."""
        reaction_id = uuid4()
        user_id = uuid4()
        post_id = uuid4()
        now = datetime.now(UTC)

        response = ReactionResponse(
            id=reaction_id,
            user_id=user_id,
            post_id=post_id,
            reaction_type=ReactionType.LIKE,
            created_at=now,
            updated_at=now,
        )

        assert response.id == reaction_id
        assert response.user_id == user_id
        assert response.post_id == post_id
        assert response.reaction_type == ReactionType.LIKE
        assert response.created_at == now
        assert response.updated_at == now

    def test_reaction_response_all_types(self) -> None:
        """Test reaction response for all reaction types."""
        for reaction_type in ReactionType:
            response = ReactionResponse(
                id=uuid4(),
                user_id=uuid4(),
                post_id=uuid4(),
                reaction_type=reaction_type,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            assert response.reaction_type == reaction_type

    def test_reaction_response_updated_after_creation(self) -> None:
        """Test reaction response where updated_at is after created_at."""
        now = datetime.now(UTC)
        updated = now.replace(hour=(now.hour + 1) % 24)

        response = ReactionResponse(
            id=uuid4(),
            user_id=uuid4(),
            post_id=uuid4(),
            reaction_type=ReactionType.CELEBRATE,
            created_at=now,
            updated_at=updated,
        )

        assert response.updated_at >= response.created_at

    def test_reaction_response_missing_required_field_fails(self) -> None:
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            ReactionResponse(
                id=uuid4(),
                user_id=uuid4(),
                # Missing post_id, reaction_type, timestamps
                reaction_type=ReactionType.LIKE,
            )  # type: ignore

        errors = exc_info.value.errors()
        assert any(err["type"] == "missing" for err in errors)

    def test_reaction_response_from_attributes(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        config = ReactionResponse.model_config
        assert config.get("from_attributes") is True


class TestReactionDetailResponse:
    """Tests for ReactionDetailResponse schema."""

    def test_valid_reaction_detail_response(self) -> None:
        """Test valid detailed reaction response with all fields."""
        reaction_id = uuid4()
        user_id = uuid4()
        post_id = uuid4()
        now = datetime.now(UTC)

        response = ReactionDetailResponse(
            id=reaction_id,
            user_id=user_id,
            post_id=post_id,
            reaction_type=ReactionType.LOVE,
            created_at=now,
            updated_at=now,
            user_name="John Doe",
            user_avatar_url="https://example.com/avatars/johndoe.jpg",
        )

        assert response.id == reaction_id
        assert response.user_id == user_id
        assert response.post_id == post_id
        assert response.reaction_type == ReactionType.LOVE
        assert response.user_name == "John Doe"
        assert response.user_avatar_url == "https://example.com/avatars/johndoe.jpg"

    def test_reaction_detail_without_user_info(self) -> None:
        """Test detailed reaction response without optional user info."""
        response = ReactionDetailResponse(
            id=uuid4(),
            user_id=uuid4(),
            post_id=uuid4(),
            reaction_type=ReactionType.SUPPORT,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.user_name is None
        assert response.user_avatar_url is None

    def test_reaction_detail_with_user_name_only(self) -> None:
        """Test detailed reaction with only user name."""
        response = ReactionDetailResponse(
            id=uuid4(),
            user_id=uuid4(),
            post_id=uuid4(),
            reaction_type=ReactionType.CELEBRATE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            user_name="Jane Smith",
        )

        assert response.user_name == "Jane Smith"
        assert response.user_avatar_url is None

    def test_reaction_detail_with_avatar_only(self) -> None:
        """Test detailed reaction with only avatar URL."""
        avatar_url = "https://example.com/avatars/user123.jpg"
        response = ReactionDetailResponse(
            id=uuid4(),
            user_id=uuid4(),
            post_id=uuid4(),
            reaction_type=ReactionType.LIKE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            user_avatar_url=avatar_url,
        )

        assert response.user_name is None
        assert response.user_avatar_url == avatar_url

    def test_reaction_detail_inherits_from_reaction_response(self) -> None:
        """Test that ReactionDetailResponse inherits all ReactionResponse fields."""
        now = datetime.now(UTC)
        response = ReactionDetailResponse(
            id=uuid4(),
            user_id=uuid4(),
            post_id=uuid4(),
            reaction_type=ReactionType.LOVE,
            created_at=now,
            updated_at=now,
            user_name="Test User",
        )

        # Verify all base fields are present
        assert hasattr(response, "id")
        assert hasattr(response, "user_id")
        assert hasattr(response, "post_id")
        assert hasattr(response, "reaction_type")
        assert hasattr(response, "created_at")
        assert hasattr(response, "updated_at")

        # Verify extended fields are present
        assert hasattr(response, "user_name")
        assert hasattr(response, "user_avatar_url")

    def test_reaction_detail_all_reaction_types(self) -> None:
        """Test detailed reaction for all reaction types."""
        for reaction_type in ReactionType:
            response = ReactionDetailResponse(
                id=uuid4(),
                user_id=uuid4(),
                post_id=uuid4(),
                reaction_type=reaction_type,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                user_name=f"User for {reaction_type.value}",
            )
            assert response.reaction_type == reaction_type
            assert response.user_name == f"User for {reaction_type.value}"

    def test_reaction_detail_from_attributes(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        config = ReactionDetailResponse.model_config
        assert config.get("from_attributes") is True
