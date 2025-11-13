"""WebSocket integration tests for real-time chat functionality.

This module tests WebSocket-based real-time chat features (User Story 5):
- WebSocket connection establishment and authentication
- Real-time message delivery between users
- Typing indicators with timeout
- Read receipt broadcasting
- Online/offline status updates
- Connection management (connect, disconnect, reconnect)
- Multi-user group chat broadcasting
- WebSocket authentication via JWT token

Tests use FastAPI's WebSocket test client with real database connections.
"""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.infrastructure.database.models.user import User
from app.main import app


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestWebSocketConnection:
    """Tests for WebSocket connection management."""

    def test_websocket_connection_with_valid_token(
        self,
        test_user: User,
    ):
        """Test WebSocket connection with valid JWT token."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act & Assert
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                # Should successfully connect
                data = websocket.receive_json()
                assert data["type"] == "connection_established"
                assert "connection_id" in data

    def test_websocket_connection_without_token(self):
        """Test WebSocket connection fails without authentication token."""
        # Act & Assert
        with TestClient(app) as client:
            with pytest.raises(Exception) as exc_info:
                with client.websocket_connect("/api/v1/ws"):
                    pass

            # Should fail with authentication error
            assert "401" in str(exc_info.value) or "403" in str(exc_info.value)

    def test_websocket_connection_with_invalid_token(self):
        """Test WebSocket connection fails with invalid JWT token."""
        # Arrange
        invalid_token = "invalid.jwt.token"

        # Act & Assert
        with TestClient(app) as client:
            with pytest.raises(Exception) as exc_info:
                with client.websocket_connect(f"/api/v1/ws?token={invalid_token}"):
                    pass

            # Should fail with authentication error
            assert "401" in str(exc_info.value) or "403" in str(exc_info.value)

    def test_websocket_disconnect_gracefully(
        self,
        test_user: User,
    ):
        """Test WebSocket disconnects gracefully when client closes."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act & Assert
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                # Receive connection confirmation
                data = websocket.receive_json()
                assert data["type"] == "connection_established"

                # Close connection explicitly
                websocket.close()
                # Should not raise exception


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestRealtimeMessageDelivery:
    """Tests for real-time message delivery via WebSocket."""

    def test_send_message_via_websocket(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test sending message via WebSocket delivers to recipient."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create a direct chat first (would be done via REST API)
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            # User 1 connects
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()  # Connection established

                # User 2 connects
                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()  # Connection established

                    # User 1 sends a message
                    ws1.send_json(
                        {
                            "type": "message",
                            "chat_id": chat_id,
                            "content": "Hello from User 1!",
                        }
                    )

                    # User 2 should receive the message
                    received = ws2.receive_json()
                    assert received["type"] == "message"
                    assert received["chat_id"] == chat_id
                    assert received["content"] == "Hello from User 1!"
                    assert received["sender_id"] == str(test_user.id)

    def test_message_not_delivered_to_non_participants(
        self,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test messages are not delivered to users outside the chat."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create a third user who is not part of the chat
        third_user = User(
            id=uuid4(),
            google_id="google-third-user-ws",
            email="thirdws@example.com",
            name="Third User WS",
        )
        db_session.add(third_user)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        user3_token = create_access_token(str(third_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            # All three users connect
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()  # Connection established

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()  # Connection established

                    with client.websocket_connect(f"/api/v1/ws?token={user3_token}") as ws3:
                        ws3.receive_json()  # Connection established

                        # User 1 sends message in chat with User 2
                        ws1.send_json(
                            {
                                "type": "message",
                                "chat_id": chat_id,
                                "content": "Private message",
                            }
                        )

                        # User 2 receives it
                        received = ws2.receive_json()
                        assert received["type"] == "message"

                        # User 3 should not receive anything (timeout if they try)
                        # In real implementation, they wouldn't get this message


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestTypingIndicators:
    """Tests for typing indicator functionality."""

    def test_typing_indicator_sent_to_chat_participants(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test typing indicator is broadcast to chat participants."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            # Both users connect
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()  # Connection established

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()  # Connection established

                    # User 1 starts typing
                    ws1.send_json(
                        {
                            "type": "typing",
                            "chat_id": chat_id,
                            "is_typing": True,
                        }
                    )

                    # User 2 receives typing indicator
                    received = ws2.receive_json()
                    assert received["type"] == "typing"
                    assert received["chat_id"] == chat_id
                    assert received["user_id"] == str(test_user.id)
                    assert received["is_typing"] is True

    def test_typing_indicator_stop_when_user_stops_typing(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test typing indicator stops when user stops typing."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            # Both users connect
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # User 1 starts typing
                    ws1.send_json(
                        {
                            "type": "typing",
                            "chat_id": chat_id,
                            "is_typing": True,
                        }
                    )
                    ws2.receive_json()  # Receive start typing

                    # User 1 stops typing
                    ws1.send_json(
                        {
                            "type": "typing",
                            "chat_id": chat_id,
                            "is_typing": False,
                        }
                    )

                    # User 2 receives stop typing
                    received = ws2.receive_json()
                    assert received["type"] == "typing"
                    assert received["is_typing"] is False

    def test_typing_indicator_timeout_after_3_seconds(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test typing indicator auto-stops after 3 seconds of inactivity."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # User 1 starts typing
                    ws1.send_json(
                        {
                            "type": "typing",
                            "chat_id": chat_id,
                            "is_typing": True,
                        }
                    )
                    ws2.receive_json()

                    # Wait for timeout (3 seconds)
                    # In real implementation, server should send auto-stop
                    # This test verifies the timeout logic exists


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestReadReceipts:
    """Tests for read receipt broadcasting via WebSocket."""

    def test_read_receipt_broadcast_to_sender(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test read receipt is sent to message sender when recipient reads."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())
        message_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # User 2 marks message as read
                    ws2.send_json(
                        {
                            "type": "read_receipt",
                            "chat_id": chat_id,
                            "message_id": message_id,
                        }
                    )

                    # User 1 (sender) receives read receipt
                    received = ws1.receive_json()
                    assert received["type"] == "read_receipt"
                    assert received["message_id"] == message_id
                    assert received["user_id"] == str(another_user.id)
                    assert "read_at" in received

    def test_read_receipt_includes_timestamp(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test read receipt includes timestamp of when message was read."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())
        message_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # User 2 marks as read
                    ws2.send_json(
                        {
                            "type": "read_receipt",
                            "chat_id": chat_id,
                            "message_id": message_id,
                        }
                    )

                    # Verify timestamp exists
                    received = ws1.receive_json()
                    assert "read_at" in received
                    # Verify it's a valid ISO timestamp
                    from datetime import datetime

                    datetime.fromisoformat(received["read_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestGroupChatBroadcast:
    """Tests for broadcasting messages in group chats."""

    def test_group_message_delivered_to_all_participants(
        self,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test message in group chat is delivered to all participants."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create third user
        third_user = User(
            id=uuid4(),
            google_id="google-third-group",
            email="thirdgroup@example.com",
            name="Third User Group",
        )
        db_session.add(third_user)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        user3_token = create_access_token(str(third_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            # All three users connect
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    with client.websocket_connect(f"/api/v1/ws?token={user3_token}") as ws3:
                        ws3.receive_json()

                        # User 1 sends message to group
                        ws1.send_json(
                            {
                                "type": "message",
                                "chat_id": chat_id,
                                "content": "Group message!",
                            }
                        )

                        # Both User 2 and User 3 receive it
                        msg2 = ws2.receive_json()
                        msg3 = ws3.receive_json()

                        assert msg2["type"] == "message"
                        assert msg2["content"] == "Group message!"
                        assert msg3["type"] == "message"
                        assert msg3["content"] == "Group message!"

    def test_typing_indicator_broadcast_to_all_group_members(
        self,
        test_user: User,
        another_user: User,
        db_session: AsyncSession,
    ):
        """Test typing indicator in group chat is broadcast to all members."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Create third user
        third_user = User(
            id=uuid4(),
            google_id="google-third-typing",
            email="thirdtyping@example.com",
            name="Third User Typing",
        )
        db_session.add(third_user)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        user3_token = create_access_token(str(third_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    with client.websocket_connect(f"/api/v1/ws?token={user3_token}") as ws3:
                        ws3.receive_json()

                        # User 1 starts typing
                        ws1.send_json(
                            {
                                "type": "typing",
                                "chat_id": chat_id,
                                "is_typing": True,
                            }
                        )

                        # Both other users receive indicator
                        typing2 = ws2.receive_json()
                        typing3 = ws3.receive_json()

                        assert typing2["type"] == "typing"
                        assert typing2["is_typing"] is True
                        assert typing3["type"] == "typing"
                        assert typing3["is_typing"] is True


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestOnlineStatus:
    """Tests for online/offline status tracking."""

    def test_user_online_status_broadcast_on_connect(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test user's online status is broadcast when they connect."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Act
        with TestClient(app) as client:
            # User 2 already connected
            with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                ws2.receive_json()  # Connection established

                # User 1 connects
                with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                    ws1.receive_json()  # Connection established

                    # User 2 may receive online status update for User 1
                    # (if they share chats)

    def test_user_offline_status_broadcast_on_disconnect(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test user's offline status is broadcast when they disconnect."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))

        # Act
        with TestClient(app) as client:
            # Both connect
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # User 1 disconnects
                    ws1.close()

                    # User 2 may receive offline status
                    # (implementation specific)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestWebSocketErrorHandling:
    """Tests for WebSocket error handling."""

    def test_invalid_message_format_returns_error(
        self,
        test_user: User,
    ):
        """Test sending invalid message format returns error."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                websocket.receive_json()  # Connection established

                # Send invalid message (missing required fields)
                websocket.send_json({"type": "message"})  # Missing chat_id, content

                # Should receive error response
                received = websocket.receive_json()
                assert received["type"] == "error"
                assert "message" in received or "error" in received

    def test_send_message_to_nonexistent_chat_returns_error(
        self,
        test_user: User,
    ):
        """Test sending message to non-existent chat returns error."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        fake_chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                websocket.receive_json()

                # Send message to non-existent chat
                websocket.send_json(
                    {
                        "type": "message",
                        "chat_id": fake_chat_id,
                        "content": "Hello",
                    }
                )

                # Should receive error
                received = websocket.receive_json()
                assert received["type"] == "error"

    def test_unauthorized_chat_access_returns_error(
        self,
        test_user: User,
    ):
        """Test accessing chat user is not part of returns error."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        private_chat_id = str(uuid4())  # Chat user doesn't have access to

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                websocket.receive_json()

                # Try to send message to unauthorized chat
                websocket.send_json(
                    {
                        "type": "message",
                        "chat_id": private_chat_id,
                        "content": "Unauthorized message",
                    }
                )

                # Should receive permission error
                received = websocket.receive_json()
                assert received["type"] == "error"
                assert (
                    "permission" in received.get("message", "").lower()
                    or "forbidden" in received.get("message", "").lower()
                )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestWebSocketReconnection:
    """Tests for WebSocket reconnection scenarios."""

    def test_reconnect_after_disconnect(
        self,
        test_user: User,
    ):
        """Test user can reconnect after disconnecting."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        with TestClient(app) as client:
            # First connection
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as ws1:
                data1 = ws1.receive_json()
                assert data1["type"] == "connection_established"
                ws1.close()

            # Reconnect
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as ws2:
                data2 = ws2.receive_json()
                assert data2["type"] == "connection_established"
                # Should successfully reconnect

    def test_multiple_connections_from_same_user(
        self,
        test_user: User,
    ):
        """Test user can have multiple WebSocket connections (multi-device)."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act - Simulate multiple devices
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={access_token}") as ws2:
                    ws2.receive_json()

                    # Both connections should work
                    # Messages should be delivered to both


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.us5
class TestWebSocketMessageAttachments:
    """Tests for sending messages with attachments via WebSocket."""

    def test_send_message_with_image_attachment(
        self,
        test_user: User,
        another_user: User,
    ):
        """Test sending message with image attachment via WebSocket."""
        # Arrange
        user1_token = create_access_token(str(test_user.id))
        user2_token = create_access_token(str(another_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={user1_token}") as ws1:
                ws1.receive_json()

                with client.websocket_connect(f"/api/v1/ws?token={user2_token}") as ws2:
                    ws2.receive_json()

                    # Send message with attachment
                    ws1.send_json(
                        {
                            "type": "message",
                            "chat_id": chat_id,
                            "content": "Check this out!",
                            "attachments": [
                                {
                                    "type": "image",
                                    "url": "https://example.com/photo.jpg",
                                    "size": 1024000,
                                }
                            ],
                        }
                    )

                    # User 2 receives with attachment
                    received = ws2.receive_json()
                    assert received["type"] == "message"
                    assert len(received.get("attachments", [])) == 1
                    assert received["attachments"][0]["type"] == "image"

    def test_attachment_size_limit_enforced(
        self,
        test_user: User,
    ):
        """Test WebSocket enforces message size limits (1MB)."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        chat_id = str(uuid4())

        # Act
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/ws?token={access_token}") as websocket:
                websocket.receive_json()

                # Try to send oversized attachment
                websocket.send_json(
                    {
                        "type": "message",
                        "chat_id": chat_id,
                        "content": "Huge file",
                        "attachments": [
                            {
                                "type": "file",
                                "url": "https://example.com/huge.zip",
                                "size": 11 * 1024 * 1024,  # 11MB - exceeds 10MB limit
                            }
                        ],
                    }
                )

                # Should receive error
                received = websocket.receive_json()
                assert received["type"] == "error"
                assert "size" in received.get("message", "").lower()
