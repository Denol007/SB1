from fastapi.testclient import TestClient

from app.main import app


def test_direct_messaging_flow():
    client = TestClient(app)

    # Step 1: Create a direct chat between two users
    response = client.post(
        "/api/v1/chats/direct", json={"user_id": "00000000-0000-0000-0000-000000000001"}
    )
    assert response.status_code == 201
    chat_data = response.json()
    chat_id = chat_data["chat_id"]

    # Step 2: Connect both users via WebSocket
    with (
        client.websocket_connect(f"/ws/chats/{chat_id}") as ws_user1,
        client.websocket_connect(f"/ws/chats/{chat_id}") as ws_user2,
    ):
        # Step 3: User A sends a message, User B receives it in real-time
        ws_user1.send_json({"type": "message", "content": "Hello, User B!"})
        message = ws_user2.receive_json()
        assert message["content"] == "Hello, User B!"

        # Step 4: User B replies, User A receives it
        ws_user2.send_json({"type": "message", "content": "Hi, User A!"})
        reply = ws_user1.receive_json()
        assert reply["content"] == "Hi, User A!"

        # Step 5: Typing indicators sent and received
        ws_user1.send_json({"type": "typing"})
        typing_indicator = ws_user2.receive_json()
        assert typing_indicator["type"] == "typing"

        # Step 6: User B marks message as read, User A receives read receipt
        ws_user2.send_json({"type": "read", "message_id": message["id"]})
        read_receipt = ws_user1.receive_json()
        assert read_receipt["type"] == "read"

    # Step 7: Verify message persistence via REST API
    response = client.get(f"/api/v1/chats/{chat_id}/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello, User B!"
    assert messages[1]["content"] == "Hi, User A!"
