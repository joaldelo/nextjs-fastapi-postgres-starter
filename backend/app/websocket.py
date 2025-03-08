from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import SessionLocal
from app.core.logging import logger
from app.models import Thread, Message
from app.schemas import MessageCreate
from app.crud import get_thread, create_message, get_thread_messages
from app.chatbot import SimpleChatbot

class WebSocketMessage(BaseModel):
    """Schema for incoming WebSocket messages."""
    content: str = Field(..., min_length=1)
    message_type: str = Field(default="chat")

class WebSocketResponse(BaseModel):
    """Schema for outgoing WebSocket messages."""
    type: str
    data: dict

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format with timezone information."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

class ConnectionManager:
    """Manages WebSocket connections for different chat threads."""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, thread_id: int) -> None:
        """
        Establish a new WebSocket connection for a specific thread.
        
        Args:
            websocket: The WebSocket connection to establish
            thread_id: The ID of the thread to connect to
        """
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

    async def heartbeat(self, websocket: WebSocket) -> bool:
        """
        Send a ping message to check if the connection is alive.
        
        Args:
            websocket: The WebSocket connection to check
            
        Returns:
            bool: True if the connection is alive, False otherwise
        """
        try:
            await websocket.send_json({"type": "ping"})
            return True
        except Exception:
            return False

    async def check_connections(self, thread_id: int) -> None:
        """
        Check all connections in a thread and remove dead ones.
        
        Args:
            thread_id: The ID of the thread to check
        """
        if thread_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[thread_id]:
                if not await self.heartbeat(connection):
                    dead_connections.append(connection)
            
            for dead_connection in dead_connections:
                self.disconnect(dead_connection, thread_id)

    def disconnect(self, websocket: WebSocket, thread_id: int) -> None:
        """
        Disconnect a WebSocket connection from a specific thread.
        
        Args:
            websocket: The WebSocket connection to disconnect
            thread_id: The ID of the thread to disconnect from
        """
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

    async def broadcast_to_thread(self, message: dict, thread_id: int) -> None:
        """
        Broadcast a message to all connections in a specific thread.
        
        Args:
            message: The message to broadcast
            thread_id: The ID of the thread to broadcast to
        """
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

class ChatHandler:
    """Handles chat-related operations and message processing."""
    
    def __init__(self, db: Session, thread_id: int):
        self.db = db
        self.thread_id = thread_id
        self.chatbot = SimpleChatbot()

    def verify_thread(self) -> Optional[Thread]:
        """Verify that the thread exists."""
        return get_thread(self.db, self.thread_id)

    async def process_user_message(self, message: WebSocketMessage) -> tuple[Message, Message]:
        """
        Process a user message and generate a bot response.
        
        Args:
            message: The validated WebSocket message
            
        Returns:
            A tuple containing the user's message and the bot's response
        """
        # Create user message
        user_message = MessageCreate(content=message.content, role="user")
        db_message = create_message(self.db, user_message, self.thread_id)
        logger.info("Created user message", extra={"thread_id": self.thread_id, "message_id": db_message.id})

        # Get conversation history and generate bot response
        conversation_history = get_thread_messages(self.db, self.thread_id)
        history_dict = [{"role": msg.role, "content": msg.content} for msg in conversation_history]
        bot_response = self.chatbot.generate_response(message.content, history_dict)
        
        # Create bot message
        bot_message = MessageCreate(content=bot_response, role="assistant")
        db_bot_message = create_message(self.db, bot_message, self.thread_id)
        logger.info("Created bot response", extra={"thread_id": self.thread_id, "message_id": db_bot_message.id})
        
        return db_message, db_bot_message

    def format_message_response(self, message: Message) -> WebSocketResponse:
        """Format a message for WebSocket response."""
        return WebSocketResponse(
            type="message",
            data={
                "id": message.id,
                "content": message.content,
                "role": message.role,
                "created_at": format_datetime(message.created_at),
                "thread_id": message.thread_id
            }
        )

manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, thread_id: int):
    """
    Main WebSocket handler that processes incoming connections and messages.
    
    Args:
        websocket: The WebSocket connection
        thread_id: The ID of the thread to handle
    """
    db = SessionLocal()
    try:
        await manager.connect(websocket, thread_id)
        
        chat_handler = ChatHandler(db, thread_id)
        if not chat_handler.verify_thread():
            logger.error("Thread not found", extra={"thread_id": thread_id})
            await websocket.close(code=4004, reason="Thread not found")
            return

        logger.info("Starting message loop", extra={"thread_id": thread_id})
        while True:
            try:
                # Check connection health periodically
                await manager.check_connections(thread_id)
                
                # Receive and validate message
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                message_data = WebSocketMessage.parse_raw(data)
                logger.info(
                    "Received message from client",
                    extra={
                        "thread_id": thread_id,
                        "content_length": len(message_data.content),
                        "message_type": message_data.message_type
                    }
                )
                
                # Process messages and broadcast responses
                user_message, bot_message = await chat_handler.process_user_message(message_data)
                await manager.broadcast_to_thread(
                    chat_handler.format_message_response(user_message).dict(),
                    thread_id
                )
                await manager.broadcast_to_thread(
                    chat_handler.format_message_response(bot_message).dict(),
                    thread_id
                )
            except ValueError as e:
                # Handle validation errors
                error_response = WebSocketResponse(
                    type="error",
                    data={"message": "Invalid message format", "details": str(e)}
                )
                await websocket.send_json(error_response.dict())

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", extra={"thread_id": thread_id})
        manager.disconnect(websocket, thread_id)
    except Exception as e:
        logger.error("WebSocket error", extra={"thread_id": thread_id, "error": str(e)})
        manager.disconnect(websocket, thread_id)
        await websocket.close(code=1011, reason=str(e))
    finally:
        db.close()
        logger.debug("Database session closed", extra={"thread_id": thread_id}) 