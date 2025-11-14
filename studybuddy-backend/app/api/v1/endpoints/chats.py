import logging
import uuid
from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

router = APIRouter(prefix="/chats", tags=["Chats"])

# Mock database
chats_db = []


class ChatCreateRequest(BaseModel):
    user_id: UUID


class ChatResponse(BaseModel):
    chat_id: UUID
    user_id: UUID


connected_clients: list[WebSocket] = []
# Manage connections per chat_id
chat_connections = defaultdict(list)

logger = logging.getLogger("websocket")


@router.post("/direct", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_direct_chat(request: ChatCreateRequest):
    """Create a direct chat between two users."""
    # Generate a unique chat_id
    chat = {
        "chat_id": uuid.uuid4(),
        "user_id": request.user_id,
    }
    chats_db.append(chat)
    logger.info(f"Created chat with chat_id: {chat['chat_id']} for user_id: {request.user_id}")
    return chat


@router.websocket("/ws/chats/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: UUID):
    logger.info(f"WebSocket connection attempt for chat_id: {chat_id}")
    try:
        await websocket.accept()
        logger.info(f"Accepted WebSocket connection for chat_id: {chat_id}")
        chat_connections[chat_id].append(websocket)
        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"Received data: {data} from chat_id: {chat_id}")
                for client in chat_connections[chat_id]:
                    if client != websocket:
                        await client.send_json(data)
            except Exception as e:
                logger.error(f"Error during message handling: {e}")
                break
    except WebSocketDisconnect as e:
        logger.warning(f"WebSocketDisconnect: {e} for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Unexpected error during WebSocket connection: {e}")
    finally:
        if websocket in chat_connections[chat_id]:
            chat_connections[chat_id].remove(websocket)
        if not chat_connections[chat_id]:
            del chat_connections[chat_id]
        logger.info(f"WebSocket connection closed for chat_id: {chat_id}")
