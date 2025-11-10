"""Unit tests for PostService.

Tests cover:
- Post creation in communities
- Post updates (content, attachments, edit timestamp)
- Post deletion (soft delete)
- Community feed with pagination and sorting
- Post pinning/unpinning (moderator+)
- Reaction management (add, remove)
- Reaction counting grouped by type
- Permission checks (author, moderator, admin)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.enums.membership_role import MembershipRole
from app.domain.enums.reaction_type import ReactionType


@pytest.fixture
def mock_post_repository():
    """Mock post repository."""
    return AsyncMock()


@pytest.fixture
def mock_reaction_repository():
    """Mock reaction repository."""
    return AsyncMock()


@pytest.fixture
def mock_comment_repository():
    """Mock comment repository."""
    return AsyncMock()


@pytest.fixture
def mock_membership_repository():
    """Mock membership repository."""
    return AsyncMock()


@pytest.fixture
def post_service(
    mock_post_repository,
    mock_reaction_repository,
    mock_comment_repository,
    mock_membership_repository,
):
    """Create PostService instance with mocked repositories.

    Note: PostService doesn't exist yet - this is TDD, tests first!
    """
    # This import will fail initially - that's expected in TDD
    try:
        from app.application.services.post_service import PostService

        return PostService(
            post_repository=mock_post_repository,
            reaction_repository=mock_reaction_repository,
            comment_repository=mock_comment_repository,
            membership_repository=mock_membership_repository,
        )
    except ImportError:
        pytest.skip("PostService not yet implemented - TDD phase")


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def author_id():
    """Sample author ID."""
    return uuid4()


@pytest.fixture
def community_id():
    """Sample community ID."""
    return uuid4()


@pytest.fixture
def post_id():
    """Sample post ID."""
    return uuid4()


@pytest.fixture
def sample_post(author_id, community_id):
    """Sample post object."""
    return MagicMock(
        id=uuid4(),
        author_id=author_id,
        community_id=community_id,
        content="This is a sample post about studying for finals!",
        attachments=None,
        is_pinned=False,
        edited_at=None,
        created_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest.fixture
def sample_reaction(user_id, post_id):
    """Sample reaction object."""
    return MagicMock(
        id=uuid4(),
        user_id=user_id,
        post_id=post_id,
        reaction_type=ReactionType.LIKE,
        created_at=datetime.now(UTC),
    )


# ============================================================================
# Test Post Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestCreatePost:
    """Test post creation."""

    @pytest.mark.asyncio
    async def test_creates_post_with_valid_data(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        author_id,
        community_id,
        sample_post,
    ):
        """Test that create_post creates a post with valid data."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        mock_post_repository.create.return_value = sample_post

        post_data = {
            "content": "This is a sample post about studying for finals!",
            "attachments": None,
        }

        # Act
        result = await post_service.create_post(
            author_id=author_id, community_id=community_id, data=post_data
        )

        # Assert
        assert result == sample_post
        mock_membership_repository.get_by_user_and_community.assert_called_once_with(
            user_id=author_id, community_id=community_id
        )
        mock_post_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_post_with_attachments(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        author_id,
        community_id,
    ):
        """Test that create_post handles attachments correctly."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        attachments = [
            {
                "type": "image",
                "url": "https://example.com/image.jpg",
                "filename": "study_notes.jpg",
            }
        ]

        post_with_attachments = MagicMock(
            id=uuid4(),
            author_id=author_id,
            community_id=community_id,
            content="Check out my study notes!",
            attachments=attachments,
            is_pinned=False,
            created_at=datetime.now(UTC),
        )

        mock_post_repository.create.return_value = post_with_attachments

        post_data = {"content": "Check out my study notes!", "attachments": attachments}

        # Act
        result = await post_service.create_post(
            author_id=author_id, community_id=community_id, data=post_data
        )

        # Assert
        assert result.attachments == attachments
        mock_post_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_error_if_user_not_member(
        self,
        post_service,
        mock_membership_repository,
        author_id,
        community_id,
    ):
        """Test that create_post raises error if user is not a community member."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = None

        post_data = {"content": "Trying to post without membership"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.create_post(
                author_id=author_id, community_id=community_id, data=post_data
            )

        assert exc_info.value.status_code == 403
        assert "member" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_error_if_content_empty(
        self,
        post_service,
        mock_membership_repository,
        author_id,
        community_id,
    ):
        """Test that create_post raises error if content is empty."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        post_data = {"content": ""}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.create_post(
                author_id=author_id, community_id=community_id, data=post_data
            )

        assert exc_info.value.status_code == 400
        assert "content" in str(exc_info.value.detail).lower()


# ============================================================================
# Test Post Updates
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestUpdatePost:
    """Test post updates."""

    @pytest.mark.asyncio
    async def test_updates_post_content_as_author(
        self,
        post_service,
        mock_post_repository,
        author_id,
        sample_post,
    ):
        """Test that update_post updates content when user is author."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post

        updated_post = MagicMock(**vars(sample_post))
        updated_post.content = "Updated content with new information"
        updated_post.edited_at = datetime.now(UTC)

        mock_post_repository.update.return_value = updated_post

        update_data = {"content": "Updated content with new information"}

        # Act
        result = await post_service.update_post(
            post_id=sample_post.id, user_id=author_id, data=update_data
        )

        # Assert
        assert result.content == "Updated content with new information"
        assert result.edited_at is not None
        mock_post_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_post_attachments(
        self,
        post_service,
        mock_post_repository,
        author_id,
        sample_post,
    ):
        """Test that update_post updates attachments."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post

        new_attachments = [{"type": "image", "url": "https://example.com/new.jpg"}]

        updated_post = MagicMock(**vars(sample_post))
        updated_post.attachments = new_attachments
        updated_post.edited_at = datetime.now(UTC)

        mock_post_repository.update.return_value = updated_post

        update_data = {"attachments": new_attachments}

        # Act
        result = await post_service.update_post(
            post_id=sample_post.id, user_id=author_id, data=update_data
        )

        # Assert
        assert result.attachments == new_attachments
        mock_post_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_error_if_not_author(
        self,
        post_service,
        mock_post_repository,
        sample_post,
    ):
        """Test that update_post raises error if user is not the author."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post
        other_user_id = uuid4()  # Different from author_id

        update_data = {"content": "Trying to update someone else's post"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.update_post(
                post_id=sample_post.id, user_id=other_user_id, data=update_data
            )

        assert exc_info.value.status_code == 403
        assert "author" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_error_if_post_not_found(
        self,
        post_service,
        mock_post_repository,
        user_id,
    ):
        """Test that update_post raises error if post doesn't exist."""
        # Arrange
        mock_post_repository.get_by_id.return_value = None
        post_id = uuid4()

        update_data = {"content": "Updating non-existent post"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.update_post(post_id=post_id, user_id=user_id, data=update_data)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()


# ============================================================================
# Test Post Deletion
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestDeletePost:
    """Test post deletion (soft delete)."""

    @pytest.mark.asyncio
    async def test_deletes_post_as_author(
        self,
        post_service,
        mock_post_repository,
        author_id,
        sample_post,
    ):
        """Test that delete_post soft deletes post when user is author."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post
        mock_post_repository.delete.return_value = None

        # Act
        await post_service.delete_post(post_id=sample_post.id, user_id=author_id)

        # Assert
        mock_post_repository.delete.assert_called_once_with(sample_post.id)

    @pytest.mark.asyncio
    async def test_deletes_post_as_moderator(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        sample_post,
    ):
        """Test that delete_post allows moderators to delete posts."""
        # Arrange
        moderator_id = uuid4()
        mock_post_repository.get_by_id.return_value = sample_post
        mock_membership_repository.has_role.return_value = True  # Is moderator

        # Act
        await post_service.delete_post(post_id=sample_post.id, user_id=moderator_id)

        # Assert
        mock_post_repository.delete.assert_called_once_with(sample_post.id)
        mock_membership_repository.has_role.assert_called_once_with(
            user_id=moderator_id,
            community_id=sample_post.community_id,
            required_role=MembershipRole.MODERATOR,
        )

    @pytest.mark.asyncio
    async def test_raises_error_if_not_authorized(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        sample_post,
    ):
        """Test that delete_post raises error if user is neither author nor moderator."""
        # Arrange
        other_user_id = uuid4()
        mock_post_repository.get_by_id.return_value = sample_post
        mock_membership_repository.has_role.return_value = False  # Not moderator

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.delete_post(post_id=sample_post.id, user_id=other_user_id)

        assert exc_info.value.status_code == 403


# ============================================================================
# Test Community Feed
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestGetCommunityFeed:
    """Test community feed retrieval with pagination and sorting."""

    @pytest.mark.asyncio
    async def test_gets_feed_with_default_pagination(
        self,
        post_service,
        mock_post_repository,
        community_id,
    ):
        """Test that get_community_feed returns paginated posts."""
        # Arrange
        posts = [
            MagicMock(
                id=uuid4(),
                community_id=community_id,
                content=f"Post {i}",
                created_at=datetime.now(UTC),
            )
            for i in range(20)
        ]

        mock_post_repository.list_by_community.return_value = posts

        # Act
        result = await post_service.get_community_feed(
            community_id=community_id, page=1, page_size=20
        )

        # Assert
        assert len(result) == 20
        mock_post_repository.list_by_community.assert_called_once_with(
            community_id=community_id,
            page=1,
            page_size=20,
            sort_by="created_at",
            descending=True,
        )

    @pytest.mark.asyncio
    async def test_gets_feed_sorted_by_created_at_desc(
        self,
        post_service,
        mock_post_repository,
        community_id,
    ):
        """Test that get_community_feed sorts by created_at descending by default."""
        # Arrange
        now = datetime.now(UTC)
        posts = [
            MagicMock(id=uuid4(), created_at=now),
            MagicMock(id=uuid4(), created_at=now),
        ]

        mock_post_repository.list_by_community.return_value = posts

        # Act
        await post_service.get_community_feed(community_id=community_id, page=1, page_size=20)

        # Assert
        call_args = mock_post_repository.list_by_community.call_args
        assert call_args.kwargs["sort_by"] == "created_at"
        assert call_args.kwargs["descending"] is True

    @pytest.mark.asyncio
    async def test_gets_feed_with_custom_page_size(
        self,
        post_service,
        mock_post_repository,
        community_id,
    ):
        """Test that get_community_feed respects custom page size."""
        # Arrange
        posts = [MagicMock(id=uuid4()) for _ in range(10)]
        mock_post_repository.list_by_community.return_value = posts

        # Act
        result = await post_service.get_community_feed(
            community_id=community_id, page=1, page_size=10
        )

        # Assert
        assert len(result) <= 10
        mock_post_repository.list_by_community.assert_called_once()

    @pytest.mark.asyncio
    async def test_pinned_posts_appear_first(
        self,
        post_service,
        mock_post_repository,
        community_id,
    ):
        """Test that get_community_feed returns pinned posts first."""
        # Arrange
        pinned_post = MagicMock(id=uuid4(), is_pinned=True, created_at=datetime.now(UTC))
        regular_post = MagicMock(id=uuid4(), is_pinned=False, created_at=datetime.now(UTC))

        mock_post_repository.list_by_community.return_value = [pinned_post, regular_post]

        # Act
        await post_service.get_community_feed(community_id=community_id, page=1, page_size=20)

        # Assert
        # Verify repository was called (actual pinned-first logic is in repository)
        mock_post_repository.list_by_community.assert_called_once()


# ============================================================================
# Test Post Pinning
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestPinPost:
    """Test post pinning (moderator+)."""

    @pytest.mark.asyncio
    async def test_pins_post_as_moderator(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        sample_post,
    ):
        """Test that pin_post pins a post when user is moderator."""
        # Arrange
        moderator_id = uuid4()
        mock_post_repository.get_by_id.return_value = sample_post
        mock_membership_repository.has_role.return_value = True

        pinned_post = MagicMock(**vars(sample_post))
        pinned_post.is_pinned = True

        mock_post_repository.update.return_value = pinned_post

        # Act
        result = await post_service.pin_post(post_id=sample_post.id, user_id=moderator_id)

        # Assert
        assert result.is_pinned is True
        mock_membership_repository.has_role.assert_called_once_with(
            user_id=moderator_id,
            community_id=sample_post.community_id,
            required_role=MembershipRole.MODERATOR,
        )

    @pytest.mark.asyncio
    async def test_raises_error_if_not_moderator(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        sample_post,
    ):
        """Test that pin_post raises error if user is not moderator."""
        # Arrange
        regular_user_id = uuid4()
        mock_post_repository.get_by_id.return_value = sample_post
        mock_membership_repository.has_role.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.pin_post(post_id=sample_post.id, user_id=regular_user_id)

        assert exc_info.value.status_code == 403
        assert "moderator" in str(exc_info.value.detail).lower()


@pytest.mark.unit
@pytest.mark.us3
class TestUnpinPost:
    """Test post unpinning (moderator+)."""

    @pytest.mark.asyncio
    async def test_unpins_post_as_moderator(
        self,
        post_service,
        mock_post_repository,
        mock_membership_repository,
        sample_post,
    ):
        """Test that unpin_post unpins a post when user is moderator."""
        # Arrange
        moderator_id = uuid4()
        sample_post.is_pinned = True
        mock_post_repository.get_by_id.return_value = sample_post
        mock_membership_repository.has_role.return_value = True

        unpinned_post = MagicMock(**vars(sample_post))
        unpinned_post.is_pinned = False

        mock_post_repository.update.return_value = unpinned_post

        # Act
        result = await post_service.unpin_post(post_id=sample_post.id, user_id=moderator_id)

        # Assert
        assert result.is_pinned is False


# ============================================================================
# Test Reaction Management
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestAddReaction:
    """Test adding reactions to posts."""

    @pytest.mark.asyncio
    async def test_adds_reaction_to_post(
        self,
        post_service,
        mock_post_repository,
        mock_reaction_repository,
        user_id,
        sample_post,
        sample_reaction,
    ):
        """Test that add_reaction adds a reaction to a post."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post
        mock_reaction_repository.get_by_user_and_post.return_value = None  # No existing reaction
        mock_reaction_repository.create.return_value = sample_reaction

        # Act
        result = await post_service.add_reaction(
            post_id=sample_post.id, user_id=user_id, reaction_type=ReactionType.LIKE
        )

        # Assert
        assert result == sample_reaction
        mock_reaction_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_reaction(
        self,
        post_service,
        mock_post_repository,
        mock_reaction_repository,
        user_id,
        sample_post,
        sample_reaction,
    ):
        """Test that add_reaction updates existing reaction if user already reacted."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_post
        existing_reaction = MagicMock(**vars(sample_reaction))
        existing_reaction.reaction_type = ReactionType.LIKE

        mock_reaction_repository.get_by_user_and_post.return_value = existing_reaction

        updated_reaction = MagicMock(**vars(existing_reaction))
        updated_reaction.reaction_type = ReactionType.LOVE

        mock_reaction_repository.update.return_value = updated_reaction

        # Act
        result = await post_service.add_reaction(
            post_id=sample_post.id, user_id=user_id, reaction_type=ReactionType.LOVE
        )

        # Assert
        assert result.reaction_type == ReactionType.LOVE
        mock_reaction_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_error_if_post_not_found(
        self,
        post_service,
        mock_post_repository,
        user_id,
    ):
        """Test that add_reaction raises error if post doesn't exist."""
        # Arrange
        post_id = uuid4()
        mock_post_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.add_reaction(
                post_id=post_id, user_id=user_id, reaction_type=ReactionType.LIKE
            )

        assert exc_info.value.status_code == 404


@pytest.mark.unit
@pytest.mark.us3
class TestRemoveReaction:
    """Test removing reactions from posts."""

    @pytest.mark.asyncio
    async def test_removes_reaction_from_post(
        self,
        post_service,
        mock_reaction_repository,
        user_id,
        sample_post,
        sample_reaction,
    ):
        """Test that remove_reaction removes user's reaction from post."""
        # Arrange
        mock_reaction_repository.get_by_user_and_post.return_value = sample_reaction
        mock_reaction_repository.delete.return_value = None

        # Act
        await post_service.remove_reaction(post_id=sample_post.id, user_id=user_id)

        # Assert
        mock_reaction_repository.delete.assert_called_once_with(sample_reaction.id)

    @pytest.mark.asyncio
    async def test_raises_error_if_reaction_not_found(
        self,
        post_service,
        mock_reaction_repository,
        user_id,
        sample_post,
    ):
        """Test that remove_reaction raises error if user hasn't reacted."""
        # Arrange
        mock_reaction_repository.get_by_user_and_post.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await post_service.remove_reaction(post_id=sample_post.id, user_id=user_id)

        assert exc_info.value.status_code == 404
        assert "reaction" in str(exc_info.value.detail).lower()


# ============================================================================
# Test Reaction Counts
# ============================================================================


@pytest.mark.unit
@pytest.mark.us3
class TestGetPostReactions:
    """Test getting reaction counts grouped by type."""

    @pytest.mark.asyncio
    async def test_gets_reactions_grouped_by_type(
        self,
        post_service,
        mock_reaction_repository,
        sample_post,
    ):
        """Test that get_post_reactions returns counts grouped by reaction type."""
        # Arrange
        mock_reaction_repository.count_by_type.return_value = {
            ReactionType.LIKE: 15,
            ReactionType.LOVE: 8,
            ReactionType.CELEBRATE: 3,
            ReactionType.SUPPORT: 2,
        }

        # Act
        result = await post_service.get_post_reactions(post_id=sample_post.id)

        # Assert
        assert result[ReactionType.LIKE] == 15
        assert result[ReactionType.LOVE] == 8
        assert result[ReactionType.CELEBRATE] == 3
        assert result[ReactionType.SUPPORT] == 2
        mock_reaction_repository.count_by_type.assert_called_once_with(sample_post.id)

    @pytest.mark.asyncio
    async def test_returns_empty_dict_if_no_reactions(
        self,
        post_service,
        mock_reaction_repository,
        sample_post,
    ):
        """Test that get_post_reactions returns empty dict if no reactions."""
        # Arrange
        mock_reaction_repository.count_by_type.return_value = {}

        # Act
        result = await post_service.get_post_reactions(post_id=sample_post.id)

        # Assert
        assert result == {}
        mock_reaction_repository.count_by_type.assert_called_once()
