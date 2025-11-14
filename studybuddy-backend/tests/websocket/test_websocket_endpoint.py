from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_websocket_connection():
    client = TestClient(app)
    chat_id = uuid4()

    with client.websocket_connect(f"/ws/chats/{chat_id}") as websocket:
        websocket.send_json({"message": "Hello, WebSocket!"})
        response = websocket.receive_json()
        assert response["message"] == "Hello, WebSocket!"
