from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
from datetime import datetime

from app.core.database import SessionLocal
from app.core.logging import logger
from app.models import Thread, Message
from app.schemas import MessageCreate
from app.crud import get_thread, create_message, get_thread_messages
from app.chatbot import SimpleChatbot

class ConnectionManager:
    def __init__(self):
        # Store active connections per thread
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, thread_id: int):
        await websocket.accept()
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = []
        self.active_connections[thread_id].append(websocket)
        logger.info(
            "New WebSocket connection established",
            extra={
                "thread_id": thread_id,
                "total_connections": len(self.active_connections[thread_id])
            }
        )

    def disconnect(self, websocket: WebSocket, thread_id: int):
        if thread_id in self.active_connections:
            self.active_connections[thread_id].remove(websocket)
            remaining = len(self.active_connections.get(thread_id, []))
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]
            logger.info(
                "WebSocket connection closed",
                extra={
                    "thread_id": thread_id,
                    "remaining_connections": remaining
                }
            )

    async def broadcast_to_thread(self, message: dict, thread_id: int):
        if thread_id in self.active_connections:
            client_count = len(self.active_connections[thread_id])
            logger.info(
                "Broadcasting message",
                extra={
                    "thread_id": thread_id,
                    "client_count": client_count,
                    "message_type": message.get("type")
                }
            )
            for connection in self.active_connections[thread_id]:
                try:
                    await connection.send_json(message)
                    logger.debug(
                        "Message broadcast successful",
                        extra={
                            "thread_id": thread_id,
                            "message_type": message.get("type")
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Failed to broadcast message",
                        extra={
                            "thread_id": thread_id,
                            "error": str(e),
                            "message_type": message.get("type")
                        }
                    )

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format with timezone information."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

manager = ConnectionManager()
chatbot = SimpleChatbot()

async def handle_websocket(websocket: WebSocket, thread_id: int):
    db = SessionLocal()
    try:
        await manager.connect(websocket, thread_id)
        
        # Verify thread exists
        db_thread = get_thread(db, thread_id)
        if not db_thread:
            logger.error("Thread not found", extra={"thread_id": thread_id})
            await websocket.close(code=4004, reason="Thread not found")
            return

        logger.info("Starting message loop", extra={"thread_id": thread_id})
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            logger.info(
                "Received message from client",
                extra={
                    "thread_id": thread_id,
                    "content_length": len(message_data.get("content", ""))
                }
            )
            
            # Create user message
            user_message = MessageCreate(
                content=message_data["content"],
                role="user"
            )
            db_message = create_message(db, user_message, thread_id)
            logger.info(
                "Created user message",
                extra={
                    "thread_id": thread_id,
                    "message_id": db_message.id
                }
            )
            
            # Broadcast user message to all clients in the thread
            await manager.broadcast_to_thread(
                {
                    "type": "message",
                    "data": {
                        "id": db_message.id,
                        "content": db_message.content,
                        "role": db_message.role,
                        "created_at": format_datetime(db_message.created_at),
                        "thread_id": db_message.thread_id
                    }
                },
                thread_id
            )
            
            # Get conversation history
            conversation_history = get_thread_messages(db, thread_id)
            history_dict = [{"role": msg.role, "content": msg.content} for msg in conversation_history]
            
            # Generate and create bot response
            bot_response = chatbot.generate_response(message_data["content"], history_dict)
            bot_message = MessageCreate(
                content=bot_response,
                role="assistant"
            )
            db_bot_message = create_message(db, bot_message, thread_id)
            logger.info(
                "Created bot response",
                extra={
                    "thread_id": thread_id,
                    "message_id": db_bot_message.id
                }
            )
            
            # Broadcast bot response to all clients in the thread
            await manager.broadcast_to_thread(
                {
                    "type": "message",
                    "data": {
                        "id": db_bot_message.id,
                        "content": db_bot_message.content,
                        "role": db_bot_message.role,
                        "created_at": format_datetime(db_bot_message.created_at),
                        "thread_id": db_bot_message.thread_id
                    }
                },
                thread_id
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", extra={"thread_id": thread_id})
        manager.disconnect(websocket, thread_id)
    except Exception as e:
        logger.error(
            "WebSocket error",
            extra={
                "thread_id": thread_id,
                "error": str(e)
            }
        )
        manager.disconnect(websocket, thread_id)
        await websocket.close(code=1011, reason=str(e))
    finally:
        db.close()
        logger.debug("Database session closed", extra={"thread_id": thread_id}) 