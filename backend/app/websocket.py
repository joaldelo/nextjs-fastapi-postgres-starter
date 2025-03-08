from typing import Dict, List, Optional, Tuple
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_async_db
from app.core.logging import logger
from app.models import Thread, Message
from app.schemas import MessageCreate
from app.crud import get_thread, create_message, get_thread_messages
from app.chatbot import SimpleChatbot

class WebSocketMessage(BaseModel):
    """Schema for incoming WebSocket messages."""
    content: str = Field(..., min_length=1, description="The content of the message")

class WebSocketResponse(BaseModel):
    """Schema for outgoing WebSocket messages."""
    type: str = Field(..., description="The type of response (message, error, connected, etc.)")
    data: dict = Field(..., description="The response payload")

def format_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO format with timezone information.
    
    Args:
        dt: The datetime to format
        
    Returns:
        str: The formatted datetime string in ISO format
    """
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
        # Connection is already accepted in the endpoint
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
        if thread_id not in self.active_connections:
            return

        client_count = len(self.active_connections[thread_id])
        logger.info(
            "Broadcasting message",
            extra={
                "thread_id": thread_id,
                "client_count": client_count,
                "message_type": message.get("type")
            }
        )

        failed_connections = []
        for connection in self.active_connections[thread_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    "Failed to broadcast message to client",
                    extra={
                        "thread_id": thread_id,
                        "error": str(e)
                    }
                )
                failed_connections.append(connection)
        
        # Clean up failed connections
        for connection in failed_connections:
            self.disconnect(connection, thread_id)

class ChatHandler:
    """Handles chat-related operations and message processing."""
    
    def __init__(self, db: AsyncSession, thread_id: int) -> None:
        self.db = db
        self.thread_id = thread_id
        self.chatbot = SimpleChatbot()
        logger.info(
            "ChatHandler initialized",
            extra={
                "thread_id": thread_id,
                "session_active": db.is_active,
                "session_id": id(db),
                "session_in_transaction": db.in_transaction()
            }
        )

    async def verify_thread(self) -> Optional[Thread]:
        """Verify that the thread exists and load its relationships."""
        try:
            # Check session state
            if not self.db or not self.db.is_active:
                logger.error(
                    "Invalid database session during thread verification",
                    extra={
                        "thread_id": self.thread_id,
                        "session_id": id(self.db) if self.db else None,
                        "session_active": getattr(self.db, 'is_active', None)
                    }
                )
                return None

            # Attempt to get the thread
            try:
                thread = await get_thread(self.db, self.thread_id)
                if not thread:
                    logger.error(
                        "Thread not found during verification",
                        extra={
                            "thread_id": self.thread_id,
                            "session_id": id(self.db)
                        }
                    )
                    return None
                
                return thread
                
            except Exception as db_error:
                logger.error(
                    "Database error while getting thread",
                    extra={
                        "thread_id": self.thread_id,
                        "error": str(db_error),
                        "error_type": type(db_error).__name__,
                        "session_id": id(self.db),
                        "session_active": self.db.is_active
                    }
                )
                return None

        except Exception as e:
            logger.error(
                "Unexpected error in verify_thread",
                extra={
                    "thread_id": self.thread_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "error_details": repr(e),
                    "session_id": id(self.db) if self.db else None,
                    "session_active": getattr(self.db, 'is_active', None)
                }
            )
            return None

    async def process_user_message(self, message: WebSocketMessage) -> Tuple[Message, Message]:
        """
        Process a user message and generate a bot response.
        
        Args:
            message: The validated WebSocket message
            
        Returns:
            Tuple[Message, Message]: A tuple containing (user_message, bot_message)
            
        Raises:
            ValueError: If the thread no longer exists
            Exception: For other processing errors
        """
        try:
            # Verify thread still exists
            thread = await self.verify_thread()
            if not thread:
                raise ValueError("Thread no longer exists")

            # Create user message
            user_message = MessageCreate(content=message.content, role="user")
            db_message = await create_message(self.db, user_message, self.thread_id)
            logger.info(
                "Created user message",
                extra={
                    "thread_id": self.thread_id,
                    "message_id": db_message.id,
                    "content_length": len(message.content)
                }
            )

            # Get conversation history and generate bot response
            conversation_history = await get_thread_messages(self.db, self.thread_id)
            history_dict = [{"role": msg.role, "content": msg.content} for msg in conversation_history]
            
            try:
                bot_response = await self.chatbot.generate_response(message.content, history_dict)
            except Exception as e:
                logger.error(
                    "Failed to generate bot response",
                    extra={
                        "thread_id": self.thread_id,
                        "error": str(e)
                    }
                )
                raise
            
            # Create bot message
            bot_message = MessageCreate(content=bot_response, role="assistant")
            db_bot_message = await create_message(self.db, bot_message, self.thread_id)
            logger.info(
                "Created bot response",
                extra={
                    "thread_id": self.thread_id,
                    "message_id": db_bot_message.id,
                    "content_length": len(bot_response)
                }
            )
            
            return db_message, db_bot_message
            
        except Exception as e:
            logger.error(
                "Error processing message",
                extra={
                    "thread_id": self.thread_id,
                    "error": str(e)
                }
            )
            raise

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

async def send_error_and_close(
    websocket: WebSocket,
    message: str,
    code: int,
    details: str = None
) -> None:
    """Helper function to send error response and close connection."""
    error_msg = {
        "type": "error",
        "data": {
            "message": message,
            "code": code
        }
    }
    if details:
        error_msg["data"]["details"] = details
    
    try:
        await websocket.send_json(error_msg)
        await websocket.close(code=code)
    except:
        pass

async def send_response(
    websocket: WebSocket,
    type: str,
    data: dict
) -> None:
    """Helper function to send standard response."""
    try:
        await websocket.send_json({
            "type": type,
            "data": data
        })
    except Exception as e:
        logger.error(
            "Failed to send response",
            extra={
                "type": type,
                "error": str(e)
            }
        )

async def handle_websocket(
    websocket: WebSocket,
    thread_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Main WebSocket handler that processes incoming connections and messages.
    """
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Log initial connection state
        logger.info(
            "WebSocket connection accepted",
            extra={
                "thread_id": thread_id,
                "session_id": id(db),
                "session_active": getattr(db, 'is_active', None),
                "session_in_transaction": getattr(db, 'in_transaction', lambda: None)()
            }
        )

        # Verify database session is active
        if not db or not db.is_active:
            await send_error_and_close(
                websocket,
                "Database session is not active",
                4003
            )
            return

        # Initialize chat handler
        chat_handler = ChatHandler(db, thread_id)
        
        # Verify thread exists before proceeding
        thread = await chat_handler.verify_thread()
        if not thread:
            await send_error_and_close(
                websocket,
                "Thread not found or database error",
                4004,
                f"Thread ID: {thread_id}"
            )
            return

        # Add to connection manager only after successful verification
        await manager.connect(websocket, thread_id)
        
        # Send success message
        await send_response(websocket, "connected", {
            "thread_id": thread_id,
            "message": "Successfully connected to thread"
        })

        # Start message loop
        while True:
            try:
                # Receive and validate message
                data = await websocket.receive_text()
                
                # Handle ping messages
                if data == "ping":
                    await send_response(websocket, "pong", {})
                    continue

                # Parse and validate the message
                try:
                    message_data = WebSocketMessage.parse_raw(data)
                except ValueError as e:
                    await send_response(websocket, "error", {
                        "message": "Invalid message format",
                        "details": str(e)
                    })
                    continue

                # Process the message
                try:
                    user_message, bot_message = await chat_handler.process_user_message(message_data)
                    
                    # Send user message
                    user_response = chat_handler.format_message_response(user_message)
                    await manager.broadcast_to_thread(user_response.dict(), thread_id)
                    
                    # Send bot response
                    bot_response = chat_handler.format_message_response(bot_message)
                    await manager.broadcast_to_thread(bot_response.dict(), thread_id)
                    
                except Exception as e:
                    logger.error(
                        "Message processing error",
                        extra={
                            "thread_id": thread_id,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    await send_response(websocket, "error", {
                        "message": "Failed to process message",
                        "details": str(e)
                    })

            except WebSocketDisconnect:
                logger.info(
                    "WebSocket disconnected",
                    extra={"thread_id": thread_id}
                )
                break
            except Exception as e:
                logger.error(
                    "Message loop error",
                    extra={
                        "thread_id": thread_id,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                await send_error_and_close(
                    websocket,
                    "Internal server error",
                    4005,
                    str(e)
                )
                break

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected during setup",
            extra={"thread_id": thread_id}
        )
    except Exception as e:
        logger.error(
            "Critical WebSocket error",
            extra={
                "thread_id": thread_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_details": repr(e),
                "session_active": getattr(db, 'is_active', None)
            }
        )
        await send_error_and_close(
            websocket,
            "Critical connection error",
            4005,
            str(e)
        )
    finally:
        manager.disconnect(websocket, thread_id)
        try:
            await websocket.close()
        except:
            pass 