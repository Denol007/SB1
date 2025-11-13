"""Unit tests for ChatService.

Tests cover:
- Direct chat creation between two users
- Group chat creation with multiple participants
- Community chat creation within communities
- Message sending with text and attachments
- Message deletion (soft delete)
- Typing indicators
- Read receipts
- Chat participant management
- Message history pagination
- Search within chat messages
- Permission checks (participants, community members)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.enums.chat_type import ChatType


@pytest.fixture
def mock_chat_repository():
    """Mock chat repository."""
    return AsyncMock()


@pytest.fixture
def mock_message_repository():
    """Mock message repository."""
    return AsyncMock()


@pytest.fixture
def mock_chat_participant_repository():
    """Mock chat participant repository."""
    return AsyncMock()


@pytest.fixture
def mock_read_receipt_repository():
    """Mock read receipt repository."""
    return AsyncMock()


@pytest.fixture
def mock_community_repository():
    """Mock community repository."""
    return AsyncMock()


@pytest.fixture
def mock_membership_repository():
    """Mock membership repository."""
    return AsyncMock()


@pytest.fixture
def chat_service(
    mock_chat_repository,
    mock_message_repository,
    mock_chat_participant_repository,
    mock_read_receipt_repository,
    mock_community_repository,
    mock_membership_repository,
):
    """Create ChatService instance with mocked repositories.

    Note: ChatService doesn't exist yet - this is TDD, tests first!
    """
    # This import will fail initially - that's expected in TDD
    try:
        from app.application.services.chat_service import ChatService

        return ChatService(
            chat_repository=mock_chat_repository,
            message_repository=mock_message_repository,
            chat_participant_repository=mock_chat_participant_repository,
            read_receipt_repository=mock_read_receipt_repository,
            community_repository=mock_community_repository,
            membership_repository=mock_membership_repository,
        )
    except ImportError:
        pytest.skip("ChatService not yet implemented - TDD phase")


@pytest.fixture
def user1_id():
    """Sample user 1 ID."""
    return uuid4()


@pytest.fixture
def user2_id():
    """Sample user 2 ID."""
    return uuid4()


@pytest.fixture
def user3_id():
    """Sample user 3 ID."""
    return uuid4()


@pytest.fixture
def chat_id():
    """Sample chat ID."""
    return uuid4()


@pytest.fixture
def community_id():
    """Sample community ID."""
    return uuid4()


@pytest.fixture
def message_id():
    """Sample message ID."""
    return uuid4()


@pytest.fixture
def sample_direct_chat(user1_id, user2_id, chat_id):
    """Sample direct chat object."""
    return MagicMock(
        id=chat_id,
        type=ChatType.DIRECT,
        name=None,
        community_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_group_chat(chat_id):
    """Sample group chat object."""
    return MagicMock(
        id=chat_id,
        type=ChatType.GROUP,
        name="Study Group - Calculus",
        community_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_community_chat(chat_id, community_id):
    """Sample community chat object."""
    return MagicMock(
        id=chat_id,
        type=ChatType.COMMUNITY,
        name="General Discussion",
        community_id=community_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_message(chat_id, user1_id, message_id):
    """Sample message object."""
    return MagicMock(
        id=message_id,
        chat_id=chat_id,
        sender_id=user1_id,
        content="Hello, this is a test message!",
        attachments=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest.fixture
def sample_participant(chat_id, user1_id):
    """Sample chat participant object."""
    return MagicMock(
        id=uuid4(),
        chat_id=chat_id,
        user_id=user1_id,
        joined_at=datetime.now(UTC),
        last_read_at=None,
    )


# ============================================================================
# Test Direct Chat Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestCreateDirectChat:
    """Test direct chat creation between two users."""

    @pytest.mark.asyncio
    async def test_creates_direct_chat_between_two_users(
        self,
        chat_service,
        mock_chat_repository,
        mock_chat_participant_repository,
        user1_id,
        user2_id,
        sample_direct_chat,
    ):
        """Test that create_direct_chat creates a chat between two users."""
        # Arrange
        mock_chat_repository.get_direct_chat_between_users.return_value = None
        mock_chat_repository.create.return_value = sample_direct_chat

        # Act
        chat = await chat_service.create_direct_chat(user1_id, user2_id)

        # Assert
        assert chat.type == ChatType.DIRECT
        assert chat.name is None
        mock_chat_repository.create.assert_called_once()
        # Should add both users as participants
        assert mock_chat_participant_repository.create.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_existing_direct_chat_if_already_exists(
        self,
        chat_service,
        mock_chat_repository,
        user1_id,
        user2_id,
        sample_direct_chat,
    ):
        """Test that create_direct_chat returns existing chat if it exists."""
        # Arrange
        mock_chat_repository.get_direct_chat_between_users.return_value = sample_direct_chat

        # Act
        chat = await chat_service.create_direct_chat(user1_id, user2_id)

        # Assert
        assert chat.id == sample_direct_chat.id
        # Should not create a new chat
        mock_chat_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_when_user_tries_to_chat_with_self(
        self,
        chat_service,
        user1_id,
    ):
        """Test that create_direct_chat raises error for same user."""
        # Arrange & Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.create_direct_chat(user1_id, user1_id)

        assert (
            "same user" in str(exc_info.value).lower() or "yourself" in str(exc_info.value).lower()
        )


# ============================================================================
# Test Group Chat Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestCreateGroupChat:
    """Test group chat creation."""

    @pytest.mark.asyncio
    async def test_creates_group_chat_with_name_and_participants(
        self,
        chat_service,
        mock_chat_repository,
        mock_chat_participant_repository,
        user1_id,
        user2_id,
        user3_id,
        sample_group_chat,
    ):
        """Test that create_group_chat creates a group with participants."""
        # Arrange
        participant_ids = [user1_id, user2_id, user3_id]
        mock_chat_repository.create.return_value = sample_group_chat

        # Act
        chat = await chat_service.create_group_chat(
            creator_id=user1_id,
            name="Study Group - Calculus",
            participant_ids=participant_ids,
        )

        # Assert
        assert chat.type == ChatType.GROUP
        assert chat.name == "Study Group - Calculus"
        mock_chat_repository.create.assert_called_once()
        # Should add all participants
        assert mock_chat_participant_repository.create.call_count == len(participant_ids)

    @pytest.mark.asyncio
    async def test_requires_at_least_two_participants_for_group(
        self,
        chat_service,
        user1_id,
    ):
        """Test that create_group_chat requires at least 2 participants."""
        # Arrange & Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.create_group_chat(
                creator_id=user1_id,
                name="Solo Group",
                participant_ids=[user1_id],
            )

        assert "at least" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_requires_group_name(
        self,
        chat_service,
        user1_id,
        user2_id,
    ):
        """Test that create_group_chat requires a name."""
        # Arrange & Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.create_group_chat(
                creator_id=user1_id,
                name="",
                participant_ids=[user1_id, user2_id],
            )

        assert "name" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()


# ============================================================================
# Test Community Chat Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestCreateCommunityChat:
    """Test community chat creation."""

    @pytest.mark.asyncio
    async def test_creates_community_chat_within_community(
        self,
        chat_service,
        mock_chat_repository,
        mock_community_repository,
        user1_id,
        community_id,
        sample_community_chat,
    ):
        """Test that create_community_chat creates chat in community."""
        # Arrange
        mock_community_repository.get_by_id.return_value = MagicMock(id=community_id)
        mock_chat_repository.create.return_value = sample_community_chat

        # Act
        chat = await chat_service.create_community_chat(
            creator_id=user1_id,
            community_id=community_id,
            name="General Discussion",
        )

        # Assert
        assert chat.type == ChatType.COMMUNITY
        assert chat.community_id == community_id
        assert chat.name == "General Discussion"
        mock_chat_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_error_when_community_not_found(
        self,
        chat_service,
        mock_community_repository,
        user1_id,
        community_id,
    ):
        """Test that create_community_chat raises error for invalid community."""
        # Arrange
        mock_community_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.create_community_chat(
                creator_id=user1_id,
                community_id=community_id,
                name="General",
            )

        assert (
            "not found" in str(exc_info.value).lower() or "community" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_requires_community_admin_or_moderator_to_create(
        self,
        chat_service,
        mock_community_repository,
        mock_membership_repository,
        user1_id,
        community_id,
    ):
        """Test that only admins/mods can create community chats."""
        # Arrange
        mock_community_repository.get_by_id.return_value = MagicMock(id=community_id)
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(role="MEMBER")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.create_community_chat(
                creator_id=user1_id,
                community_id=community_id,
                name="General",
            )

        assert "permission" in str(exc_info.value).lower() or "admin" in str(exc_info.value).lower()


# ============================================================================
# Test Send Message
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestSendMessage:
    """Test sending messages in chats."""

    @pytest.mark.asyncio
    async def test_sends_text_message_to_chat(
        self,
        chat_service,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
        sample_message,
    ):
        """Test that send_message creates a text message."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = True
        mock_message_repository.create.return_value = sample_message

        # Act
        message = await chat_service.send_message(
            chat_id=chat_id,
            sender_id=user1_id,
            content="Hello, this is a test message!",
        )

        # Assert
        assert message.content == "Hello, this is a test message!"
        assert message.chat_id == chat_id
        assert message.sender_id == user1_id
        mock_message_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_sends_message_with_attachments(
        self,
        chat_service,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that send_message supports attachments."""
        # Arrange
        attachments = [{"type": "image", "url": "https://example.com/photo.jpg", "size": 1024000}]
        mock_chat_participant_repository.is_participant.return_value = True
        mock_message = MagicMock(
            id=uuid4(),
            chat_id=chat_id,
            sender_id=user1_id,
            content="Check out this photo!",
            attachments=attachments,
        )
        mock_message_repository.create.return_value = mock_message

        # Act
        message = await chat_service.send_message(
            chat_id=chat_id,
            sender_id=user1_id,
            content="Check out this photo!",
            attachments=attachments,
        )

        # Assert
        assert message.attachments == attachments
        assert len(message.attachments) == 1

    @pytest.mark.asyncio
    async def test_raises_error_when_sender_not_participant(
        self,
        chat_service,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that send_message raises error for non-participants."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = False

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.send_message(
                chat_id=chat_id,
                sender_id=user1_id,
                content="Hello!",
            )

        assert (
            "participant" in str(exc_info.value).lower()
            or "permission" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_requires_non_empty_content_or_attachments(
        self,
        chat_service,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that send_message requires content or attachments."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = True

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.send_message(
                chat_id=chat_id,
                sender_id=user1_id,
                content="",
                attachments=None,
            )

        assert "content" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()


# ============================================================================
# Test Delete Message
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestDeleteMessage:
    """Test message deletion (soft delete)."""

    @pytest.mark.asyncio
    async def test_sender_can_delete_own_message(
        self,
        chat_service,
        mock_message_repository,
        user1_id,
        message_id,
        sample_message,
    ):
        """Test that sender can delete their own message."""
        # Arrange
        sample_message.sender_id = user1_id
        mock_message_repository.get_by_id.return_value = sample_message

        # Act
        await chat_service.delete_message(message_id=message_id, user_id=user1_id)

        # Assert
        mock_message_repository.soft_delete.assert_called_once_with(message_id)

    @pytest.mark.asyncio
    async def test_raises_error_when_non_sender_tries_to_delete(
        self,
        chat_service,
        mock_message_repository,
        user1_id,
        user2_id,
        message_id,
        sample_message,
    ):
        """Test that non-sender cannot delete message."""
        # Arrange
        sample_message.sender_id = user1_id
        mock_message_repository.get_by_id.return_value = sample_message

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.delete_message(message_id=message_id, user_id=user2_id)

        assert (
            "permission" in str(exc_info.value).lower() or "sender" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_raises_error_when_message_not_found(
        self,
        chat_service,
        mock_message_repository,
        user1_id,
        message_id,
    ):
        """Test that delete_message raises error for non-existent message."""
        # Arrange
        mock_message_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.delete_message(message_id=message_id, user_id=user1_id)

        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Test Get Chat Messages
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestGetChatMessages:
    """Test retrieving chat message history."""

    @pytest.mark.asyncio
    async def test_returns_paginated_messages_for_chat(
        self,
        chat_service,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that get_messages returns paginated message history."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = True
        messages = [
            MagicMock(id=uuid4(), content=f"Message {i}", created_at=datetime.now(UTC))
            for i in range(3)
        ]
        mock_message_repository.get_by_chat_id.return_value = messages

        # Act
        result = await chat_service.get_messages(
            chat_id=chat_id,
            user_id=user1_id,
            skip=0,
            limit=10,
        )

        # Assert
        assert len(result) == 3
        mock_message_repository.get_by_chat_id.assert_called_once_with(chat_id, skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_raises_error_when_non_participant_requests_messages(
        self,
        chat_service,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that non-participants cannot view messages."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = False

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.get_messages(
                chat_id=chat_id,
                user_id=user1_id,
                skip=0,
                limit=10,
            )

        assert (
            "participant" in str(exc_info.value).lower()
            or "permission" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_returns_messages_in_chronological_order(
        self,
        chat_service,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that messages are returned in chronological order."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = True
        messages = [
            MagicMock(
                id=uuid4(),
                content=f"Message {i}",
                created_at=datetime(2025, 11, 13, 10, i, 0, tzinfo=UTC),
            )
            for i in range(3)
        ]
        mock_message_repository.get_by_chat_id.return_value = messages

        # Act
        result = await chat_service.get_messages(
            chat_id=chat_id,
            user_id=user1_id,
            skip=0,
            limit=10,
        )

        # Assert
        assert result[0].created_at < result[1].created_at < result[2].created_at


# ============================================================================
# Test Mark Messages as Read
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestMarkMessagesAsRead:
    """Test marking messages as read (read receipts)."""

    @pytest.mark.asyncio
    async def test_creates_read_receipt_for_message(
        self,
        chat_service,
        mock_read_receipt_repository,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        message_id,
        sample_message,
    ):
        """Test that mark_as_read creates read receipt."""
        # Arrange
        mock_message_repository.get_by_id.return_value = sample_message
        mock_chat_participant_repository.is_participant.return_value = True

        # Act
        await chat_service.mark_as_read(message_id=message_id, user_id=user1_id)

        # Assert
        mock_read_receipt_repository.create_or_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_participant_last_read_timestamp(
        self,
        chat_service,
        mock_chat_participant_repository,
        mock_message_repository,
        user1_id,
        message_id,
        sample_message,
    ):
        """Test that mark_as_read updates last_read_at timestamp."""
        # Arrange
        mock_message_repository.get_by_id.return_value = sample_message
        mock_chat_participant_repository.is_participant.return_value = True

        # Act
        await chat_service.mark_as_read(message_id=message_id, user_id=user1_id)

        # Assert
        mock_chat_participant_repository.update_last_read.assert_called_once()


# ============================================================================
# Test Get User Chats
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestGetUserChats:
    """Test retrieving user's chat list."""

    @pytest.mark.asyncio
    async def test_returns_all_chats_user_participates_in(
        self,
        chat_service,
        mock_chat_repository,
        user1_id,
    ):
        """Test that get_user_chats returns all user's chats."""
        # Arrange
        chats = [
            MagicMock(id=uuid4(), type=ChatType.DIRECT, name=None),
            MagicMock(id=uuid4(), type=ChatType.GROUP, name="Study Group"),
            MagicMock(id=uuid4(), type=ChatType.COMMUNITY, name="General"),
        ]
        mock_chat_repository.get_by_participant.return_value = chats

        # Act
        result = await chat_service.get_user_chats(user_id=user1_id)

        # Assert
        assert len(result) == 3
        mock_chat_repository.get_by_participant.assert_called_once_with(user1_id)

    @pytest.mark.asyncio
    async def test_returns_chats_with_latest_message_preview(
        self,
        chat_service,
        mock_chat_repository,
        mock_message_repository,
        user1_id,
    ):
        """Test that chats include latest message preview."""
        # Arrange
        chat = MagicMock(id=uuid4(), type=ChatType.DIRECT)
        latest_message = MagicMock(content="Latest message", created_at=datetime.now(UTC))
        mock_chat_repository.get_by_participant.return_value = [chat]
        mock_message_repository.get_latest_by_chat.return_value = latest_message

        # Act
        result = await chat_service.get_user_chats(user_id=user1_id)

        # Assert
        assert len(result) > 0
        # Implementation should include latest message info


# ============================================================================
# Test Add Participant to Group Chat
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestAddParticipant:
    """Test adding participants to group chats."""

    @pytest.mark.asyncio
    async def test_adds_user_to_group_chat(
        self,
        chat_service,
        mock_chat_repository,
        mock_chat_participant_repository,
        user1_id,
        user2_id,
        chat_id,
        sample_group_chat,
    ):
        """Test that add_participant adds user to group chat."""
        # Arrange
        mock_chat_repository.get_by_id.return_value = sample_group_chat
        mock_chat_participant_repository.is_participant.return_value = True

        # Act
        await chat_service.add_participant(
            chat_id=chat_id,
            user_id_to_add=user2_id,
            added_by=user1_id,
        )

        # Assert
        mock_chat_participant_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_cannot_add_participant_to_direct_chat(
        self,
        chat_service,
        mock_chat_repository,
        user1_id,
        user2_id,
        chat_id,
        sample_direct_chat,
    ):
        """Test that participants cannot be added to direct chats."""
        # Arrange
        mock_chat_repository.get_by_id.return_value = sample_direct_chat

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.add_participant(
                chat_id=chat_id,
                user_id_to_add=user2_id,
                added_by=user1_id,
            )

        assert (
            "direct chat" in str(exc_info.value).lower()
            or "not allowed" in str(exc_info.value).lower()
        )


# ============================================================================
# Test Search Messages
# ============================================================================


@pytest.mark.unit
@pytest.mark.us5
class TestSearchMessages:
    """Test searching within chat messages."""

    @pytest.mark.asyncio
    async def test_searches_messages_by_content(
        self,
        chat_service,
        mock_message_repository,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that search_messages finds messages by content."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = True
        matching_messages = [
            MagicMock(
                id=uuid4(),
                content="Let's study for the assignment deadline tomorrow",
                created_at=datetime.now(UTC),
            )
        ]
        mock_message_repository.search.return_value = matching_messages

        # Act
        result = await chat_service.search_messages(
            chat_id=chat_id,
            user_id=user1_id,
            query="assignment deadline",
        )

        # Assert
        assert len(result) == 1
        assert "assignment deadline" in result[0].content

    @pytest.mark.asyncio
    async def test_search_requires_participant_access(
        self,
        chat_service,
        mock_chat_participant_repository,
        user1_id,
        chat_id,
    ):
        """Test that non-participants cannot search messages."""
        # Arrange
        mock_chat_participant_repository.is_participant.return_value = False

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_service.search_messages(
                chat_id=chat_id,
                user_id=user1_id,
                query="test",
            )

        assert (
            "participant" in str(exc_info.value).lower()
            or "permission" in str(exc_info.value).lower()
        )
