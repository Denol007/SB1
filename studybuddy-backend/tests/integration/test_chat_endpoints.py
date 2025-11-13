"""Integration tests for Chat API endpoints.

This module tests the complete Chat API implementation (User Story 5):
- Direct chat creation and retrieval
- Group chat creation and management
- Community chat creation within communities
- Message sending (text and attachments)
- Message deletion and editing
- Read receipts and message history
- Participant management
- Search within messages

Tests use real database connections and actual API calls.
"""

from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domain.enums.chat_type import ChatType
from app.infrastructure.database.models.user import User


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestChatEndpoints:
    """Integration tests for chat API endpoints."""

    async def test_create_direct_chat_between_users(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test POST /api/v1/chats/direct creates direct chat."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == ChatType.DIRECT.value
        assert data["name"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_direct_chat_returns_existing_if_exists(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test creating direct chat twice returns same chat."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act - Create first time
        response1 = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id_1 = response1.json()["id"]

        # Act - Create second time
        response2 = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id_2 = response2.json()["id"]

        # Assert
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_200_OK
        assert chat_id_1 == chat_id_2

    async def test_cannot_create_direct_chat_with_self(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test cannot create direct chat with yourself."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(test_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_group_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test POST /api/v1/chats/group creates group chat."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/chats/group",
            json={
                "name": "Study Group - Algorithms",
                "participant_ids": [str(test_user.id), str(another_user.id)],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == ChatType.GROUP.value
        assert data["name"] == "Study Group - Algorithms"
        assert "id" in data

    async def test_group_chat_requires_name(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test group chat creation requires a name."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/chats/group",
            json={
                "name": "",
                "participant_ids": [str(test_user.id), str(another_user.id)],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_group_chat_requires_minimum_participants(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test group chat requires at least 2 participants."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/chats/group",
            json={
                "name": "Solo Group",
                "participant_ids": [str(test_user.id)],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_user_chats(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test GET /api/v1/chats returns user's chat list."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a direct chat first
        await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Act
        response = await async_client.get(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_chat_by_id(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test GET /api/v1/chats/{chat_id} returns chat details."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat
        create_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = create_response.json()["id"]

        # Act
        response = await async_client.get(
            f"/api/v1/chats/{chat_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == chat_id
        assert data["type"] == ChatType.DIRECT.value


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestMessageEndpoints:
    """Integration tests for message API endpoints."""

    async def test_send_message_to_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test POST /api/v1/chats/{chat_id}/messages sends message."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat first
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello! How are you?"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "Hello! How are you?"
        assert data["chat_id"] == chat_id
        assert UUID(data["sender_id"]) == test_user.id
        assert "id" in data
        assert "created_at" in data

    async def test_send_message_with_attachments(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test sending message with file attachments."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat first
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={
                "content": "Check out this file!",
                "attachments": [
                    {
                        "type": "image",
                        "url": "https://example.com/photo.jpg",
                        "size": 1024000,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["type"] == "image"

    async def test_cannot_send_empty_message(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test cannot send message without content or attachments."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat first
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": ""},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_chat_messages(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test GET /api/v1/chats/{chat_id}/messages returns message history."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Send some messages
        await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "First message"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Second message"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Act
        response = await async_client.get(
            f"/api/v1/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_messages_supports_pagination(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test message history supports pagination."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Send multiple messages
        for i in range(5):
            await async_client.post(
                f"/api/v1/chats/{chat_id}/messages",
                json={"content": f"Message {i}"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Act
        response = await async_client.get(
            f"/api/v1/chats/{chat_id}/messages?skip=0&limit=2",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    async def test_delete_own_message(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test DELETE /api/v1/messages/{message_id} deletes message."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat and send a message
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        message_response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Message to delete"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        message_id = message_response.json()["id"]

        # Act
        response = await async_client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_cannot_delete_others_message(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test cannot delete message sent by another user."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create a chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        chat_id = chat_response.json()["id"]

        # User 1 sends a message
        message_response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "User 1's message"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        message_id = message_response.json()["id"]

        # Act - User 2 tries to delete
        response = await async_client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestReadReceipts:
    """Integration tests for read receipts."""

    async def test_mark_message_as_read(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test POST /api/v1/messages/{message_id}/read marks message as read."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create a chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        chat_id = chat_response.json()["id"]

        # User 1 sends a message
        message_response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello!"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        message_id = message_response.json()["id"]

        # Act - User 2 marks as read
        response = await async_client.post(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

    async def test_get_read_receipts_for_message(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test GET /api/v1/messages/{message_id}/receipts returns read receipts."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create a chat and send a message
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        chat_id = chat_response.json()["id"]

        message_response = await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Test message"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        message_id = message_response.json()["id"]

        # User 2 marks as read
        await async_client.post(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        # Act
        response = await async_client.get(
            f"/api/v1/messages/{message_id}/receipts",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestGroupChatManagement:
    """Integration tests for group chat participant management."""

    async def test_add_participant_to_group_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test POST /api/v1/chats/{chat_id}/participants adds user to group."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a third user
        third_user = User(
            id=uuid4(),
            google_id="google-third-user",
            email="third@example.com",
            name="Third User",
        )
        db_session.add(third_user)
        await db_session.commit()

        # Create a group chat
        chat_response = await async_client.post(
            "/api/v1/chats/group",
            json={
                "name": "Study Group",
                "participant_ids": [str(test_user.id), str(another_user.id)],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/chats/{chat_id}/participants",
            json={"user_id": str(third_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    async def test_cannot_add_participant_to_direct_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test cannot add participants to direct chats."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a third user
        third_user = User(
            id=uuid4(),
            google_id="google-third-user-2",
            email="third2@example.com",
            name="Third User 2",
        )
        db_session.add(third_user)
        await db_session.commit()

        # Create a direct chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/chats/{chat_id}/participants",
            json={"user_id": str(third_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_remove_participant_from_group_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test DELETE /api/v1/chats/{chat_id}/participants/{user_id} removes user."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a third user
        third_user = User(
            id=uuid4(),
            google_id="google-third-user-3",
            email="third3@example.com",
            name="Third User 3",
        )
        db_session.add(third_user)
        await db_session.commit()

        # Create a group chat with 3 users
        chat_response = await async_client.post(
            "/api/v1/chats/group",
            json={
                "name": "Study Group",
                "participant_ids": [
                    str(test_user.id),
                    str(another_user.id),
                    str(third_user.id),
                ],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act
        response = await async_client.delete(
            f"/api/v1/chats/{chat_id}/participants/{str(third_user.id)}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestMessageSearch:
    """Integration tests for message search functionality."""

    async def test_search_messages_in_chat(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
    ):
        """Test GET /api/v1/chats/{chat_id}/messages/search finds messages."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Create a chat
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Send messages with specific content
        await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "The assignment deadline is tomorrow"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        await async_client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Random message about something else"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Act
        response = await async_client.get(
            f"/api/v1/chats/{chat_id}/messages/search?q=assignment+deadline",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("assignment deadline" in msg["content"].lower() for msg in data)

    async def test_search_requires_participant_access(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test non-participants cannot search chat messages."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))

        # Create a third user who is not in the chat
        third_user = User(
            id=uuid4(),
            google_id="google-third-user-4",
            email="third4@example.com",
            name="Third User 4",
        )
        db_session.add(third_user)
        await db_session.commit()
        user3_token = create_access_token(str(third_user.id))

        # Create a chat between user 1 and 2
        chat_response = await async_client.post(
            "/api/v1/chats/direct",
            json={"user_id": str(another_user.id)},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        chat_id = chat_response.json()["id"]

        # Act - User 3 tries to search
        response = await async_client.get(
            f"/api/v1/chats/{chat_id}/messages/search?q=test",
            headers={"Authorization": f"Bearer {user3_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
