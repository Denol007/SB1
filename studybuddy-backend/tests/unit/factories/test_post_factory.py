"""Unit tests for post, reaction, and comment factories.

Tests the factory methods for creating test data for posts, reactions, and comments.
Verifies that factories generate valid data with expected attributes.
"""

from datetime import datetime
from uuid import UUID

import pytest

from app.domain.enums.reaction_type import ReactionType
from tests.factories.post_factory import CommentFactory, PostFactory, ReactionFactory


class TestPostFactory:
    """Test suite for PostFactory."""

    def test_build_creates_post_with_required_fields(self):
        """Test that build() creates a post with all required fields."""
        post = PostFactory.build()

        assert isinstance(post["id"], UUID)
        assert isinstance(post["author_id"], UUID)
        assert isinstance(post["community_id"], UUID)
        assert isinstance(post["content"], str)
        assert len(post["content"]) > 0
        assert isinstance(post["created_at"], datetime)
        assert post["is_pinned"] is False
        assert post["edited_at"] is None
        assert post["deleted_at"] is None

    def test_build_with_custom_attributes(self):
        """Test that build() accepts custom attributes."""
        author_id = UUID("12345678-1234-5678-1234-567812345678")
        community_id = UUID("87654321-4321-8765-4321-876543218765")
        content = "Custom post content"

        post = PostFactory.build(author_id=author_id, community_id=community_id, content=content)

        assert post["author_id"] == author_id
        assert post["community_id"] == community_id
        assert post["content"] == content

    def test_with_attachments_creates_post_with_attachments(self):
        """Test that with_attachments() creates a post with image attachments."""
        post = PostFactory.with_attachments()

        assert post["attachments"] is not None
        assert isinstance(post["attachments"], list)
        assert len(post["attachments"]) > 0
        assert len(post["attachments"]) <= 3

        # Verify attachment structure
        for attachment in post["attachments"]:
            assert "type" in attachment
            assert attachment["type"] == "image"
            assert "url" in attachment
            assert "filename" in attachment
            assert "size" in attachment
            assert isinstance(attachment["size"], int)

    def test_pinned_creates_pinned_post(self):
        """Test that pinned() creates a post with is_pinned=True."""
        post = PostFactory.pinned()

        assert post["is_pinned"] is True

    def test_edited_creates_post_with_edit_timestamp(self):
        """Test that edited() creates a post with edited_at timestamp."""
        post = PostFactory.edited()

        assert post["edited_at"] is not None
        assert isinstance(post["edited_at"], datetime)
        assert post["edited_at"] >= post["created_at"]

    def test_default_attachments_is_none(self):
        """Test that default post has no attachments."""
        post = PostFactory.build()

        assert post["attachments"] is None

    def test_content_varies_between_posts(self):
        """Test that different posts have different content (randomization)."""
        post1 = PostFactory.build()
        post2 = PostFactory.build()

        # Content should be different (with extremely high probability)
        assert post1["content"] != post2["content"]


class TestReactionFactory:
    """Test suite for ReactionFactory."""

    def test_build_creates_reaction_with_required_fields(self):
        """Test that build() creates a reaction with all required fields."""
        reaction = ReactionFactory.build()

        assert isinstance(reaction["id"], UUID)
        assert isinstance(reaction["user_id"], UUID)
        assert isinstance(reaction["post_id"], UUID)
        assert isinstance(reaction["reaction_type"], ReactionType)
        assert isinstance(reaction["created_at"], datetime)

    def test_build_with_custom_attributes(self):
        """Test that build() accepts custom attributes."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        post_id = UUID("87654321-4321-8765-4321-876543218765")

        reaction = ReactionFactory.build(
            user_id=user_id, post_id=post_id, reaction_type=ReactionType.LOVE
        )

        assert reaction["user_id"] == user_id
        assert reaction["post_id"] == post_id
        assert reaction["reaction_type"] == ReactionType.LOVE

    def test_like_creates_like_reaction(self):
        """Test that like() creates a reaction with LIKE type."""
        reaction = ReactionFactory.like()

        assert reaction["reaction_type"] == ReactionType.LIKE

    def test_love_creates_love_reaction(self):
        """Test that love() creates a reaction with LOVE type."""
        reaction = ReactionFactory.love()

        assert reaction["reaction_type"] == ReactionType.LOVE

    def test_celebrate_creates_celebrate_reaction(self):
        """Test that celebrate() creates a reaction with CELEBRATE type."""
        reaction = ReactionFactory.celebrate()

        assert reaction["reaction_type"] == ReactionType.CELEBRATE

    def test_support_creates_support_reaction(self):
        """Test that support() creates a reaction with SUPPORT type."""
        reaction = ReactionFactory.support()

        assert reaction["reaction_type"] == ReactionType.SUPPORT

    def test_reaction_type_is_valid_enum(self):
        """Test that reaction_type is always a valid ReactionType enum."""
        for _ in range(10):  # Test multiple random generations
            reaction = ReactionFactory.build()
            assert reaction["reaction_type"] in ReactionType

    def test_custom_reaction_type_with_helper_methods(self):
        """Test that helper methods accept custom attributes."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        reaction = ReactionFactory.like(user_id=user_id)

        assert reaction["user_id"] == user_id
        assert reaction["reaction_type"] == ReactionType.LIKE


class TestCommentFactory:
    """Test suite for CommentFactory."""

    def test_build_creates_comment_with_required_fields(self):
        """Test that build() creates a comment with all required fields."""
        comment = CommentFactory.build()

        assert isinstance(comment["id"], UUID)
        assert isinstance(comment["author_id"], UUID)
        assert isinstance(comment["post_id"], UUID)
        assert isinstance(comment["content"], str)
        assert len(comment["content"]) > 0
        assert isinstance(comment["created_at"], datetime)
        assert comment["parent_comment_id"] is None
        assert comment["deleted_at"] is None

    def test_build_with_custom_attributes(self):
        """Test that build() accepts custom attributes."""
        author_id = UUID("12345678-1234-5678-1234-567812345678")
        post_id = UUID("87654321-4321-8765-4321-876543218765")
        content = "Custom comment content"

        comment = CommentFactory.build(author_id=author_id, post_id=post_id, content=content)

        assert comment["author_id"] == author_id
        assert comment["post_id"] == post_id
        assert comment["content"] == content

    def test_reply_creates_nested_comment(self):
        """Test that reply() creates a comment with parent_comment_id."""
        parent_id = UUID("11111111-1111-1111-1111-111111111111")

        reply = CommentFactory.reply(parent_comment_id=parent_id)

        assert reply["parent_comment_id"] == parent_id
        assert isinstance(reply["parent_comment_id"], UUID)

    def test_reply_generates_parent_id_if_not_provided(self):
        """Test that reply() generates a parent_comment_id if not provided."""
        reply = CommentFactory.reply()

        assert reply["parent_comment_id"] is not None
        assert isinstance(reply["parent_comment_id"], UUID)

    def test_short_creates_short_comment(self):
        """Test that short() creates a brief comment."""
        comment = CommentFactory.short()

        # Short comments should be less than 15 words typically
        word_count = len(comment["content"].split())
        assert word_count < 15

    def test_long_creates_long_comment(self):
        """Test that long() creates a lengthy comment."""
        comment = CommentFactory.long()

        # Long comments should be more than 50 words typically
        word_count = len(comment["content"].split())
        assert word_count > 30  # Conservative check for reliability

    def test_default_is_top_level_comment(self):
        """Test that default comment is top-level (no parent)."""
        comment = CommentFactory.build()

        assert comment["parent_comment_id"] is None

    def test_content_varies_between_comments(self):
        """Test that different comments have different content (randomization)."""
        comment1 = CommentFactory.build()
        comment2 = CommentFactory.build()

        # Content should be different (with extremely high probability)
        assert comment1["content"] != comment2["content"]

    def test_helper_methods_accept_custom_attributes(self):
        """Test that helper methods (short, long, reply) accept custom attributes."""
        author_id = UUID("12345678-1234-5678-1234-567812345678")

        short_comment = CommentFactory.short(author_id=author_id)
        long_comment = CommentFactory.long(author_id=author_id)

        assert short_comment["author_id"] == author_id
        assert long_comment["author_id"] == author_id


class TestReactionTypeEnum:
    """Test suite for ReactionType enum."""

    def test_all_reaction_types_are_defined(self):
        """Test that all expected reaction types are defined."""
        expected_types = {"like", "love", "celebrate", "support"}
        actual_types = {rt.value for rt in ReactionType}

        assert actual_types == expected_types

    def test_reaction_type_string_representation(self):
        """Test that ReactionType has correct string representation."""
        assert str(ReactionType.LIKE) == "like"
        assert str(ReactionType.LOVE) == "love"
        assert str(ReactionType.CELEBRATE) == "celebrate"
        assert str(ReactionType.SUPPORT) == "support"

    def test_from_string_creates_valid_enum(self):
        """Test that from_string() creates valid enum from string."""
        assert ReactionType.from_string("like") == ReactionType.LIKE
        assert ReactionType.from_string("LOVE") == ReactionType.LOVE
        assert ReactionType.from_string("Celebrate") == ReactionType.CELEBRATE
        assert ReactionType.from_string("SUPPORT") == ReactionType.SUPPORT

    def test_from_string_raises_on_invalid_value(self):
        """Test that from_string() raises ValueError for invalid types."""
        with pytest.raises(ValueError) as exc_info:
            ReactionType.from_string("invalid")

        assert "Invalid reaction type" in str(exc_info.value)
        assert "like, love, celebrate, support" in str(exc_info.value)

    def test_reaction_type_is_string_enum(self):
        """Test that ReactionType values are strings."""
        for reaction_type in ReactionType:
            assert isinstance(reaction_type.value, str)
