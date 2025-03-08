from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import logger
from app.models import User, Thread, Message
from app.schemas import User, ThreadCreate, Thread, MessageCreate, Message
from app.crud import (
    get_user, get_user_threads,
    get_thread, create_thread, get_thread_messages,
    create_message, get_user_by_name
)
from app.chatbot import SimpleChatbot

router = APIRouter()
chatbot = SimpleChatbot()

@router.post("/users/", response_model=User)
def create_user(user: User, db: Session = Depends(get_db)):
    try:
        db_user = get_user_by_name(db, name=user.name)
        if db_user:
            raise HTTPException(status_code=400, detail="User already exists")
        db_user = User(**user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info("User created successfully", extra={"user_name": user.name})
        return db_user
    except Exception as e:
        logger.error(
            "Failed to create user",
            extra={
                "error": str(e),
                "user_name": user.name
            }
        )
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = get_user(db, user_id)
        if db_user is None:
            logger.warning("User not found", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        logger.error(
            "Failed to get user",
            extra={
                "error": str(e),
                "user_id": user_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.post("/threads/", response_model=Thread)
def create_new_thread(thread: ThreadCreate, db: Session = Depends(get_db)):
    try:
        db_thread = create_thread(db, thread)
        logger.info(
            "Thread created successfully",
            extra={
                "thread_id": db_thread.id,
                "title": db_thread.title,
                "user_id": db_thread.user_id
            }
        )
        return db_thread
    except Exception as e:
        logger.error(
            "Failed to create thread",
            extra={
                "error": str(e),
                "title": thread.title,
                "user_id": thread.user_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to create thread")


@router.get("/threads/{thread_id}", response_model=Thread)
def read_thread(thread_id: int, db: Session = Depends(get_db)):
    try:
        db_thread = get_thread(db, thread_id)
        if db_thread is None:
            logger.warning("Thread not found", extra={"thread_id": thread_id})
            raise HTTPException(status_code=404, detail="Thread not found")
        return db_thread
    except Exception as e:
        logger.error(
            "Failed to get thread",
            extra={
                "error": str(e),
                "thread_id": thread_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to get thread")


@router.get("/users/{user_id}/threads/", response_model=List[Thread])
def read_user_threads(user_id: int, db: Session = Depends(get_db)):
    try:
        threads = get_user_threads(db, user_id)
        logger.info(
            "Retrieved user threads",
            extra={
                "user_id": user_id,
                "thread_count": len(threads)
            }
        )
        return threads
    except Exception as e:
        logger.error(
            "Failed to get user threads",
            extra={
                "error": str(e),
                "user_id": user_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to get user threads")


@router.post("/threads/{thread_id}/messages/", response_model=Message)
def create_new_message(thread_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    try:
        # Verify thread exists
        db_thread = get_thread(db, thread_id)
        if db_thread is None:
            logger.warning("Thread not found", extra={"thread_id": thread_id})
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Create user message
        db_message = create_message(db, message, thread_id)
        logger.info(
            "User message created",
            extra={
                "thread_id": thread_id,
                "message_id": db_message.id,
                "role": "user"
            }
        )
        
        # Get conversation history
        conversation_history = get_thread_messages(db, thread_id)
        history_dict = [{"role": msg.role, "content": msg.content} for msg in conversation_history]
        
        # Generate and create bot response
        bot_response = chatbot.generate_response(message.content, history_dict)
        bot_message = MessageCreate(
            content=bot_response,
            role="assistant"
        )
        db_bot_message = create_message(db, bot_message, thread_id)
        logger.info(
            "Bot response created",
            extra={
                "thread_id": thread_id,
                "message_id": db_bot_message.id,
                "role": "assistant"
            }
        )
        
        return db_message
    except Exception as e:
        logger.error(
            "Failed to create message",
            extra={
                "error": str(e),
                "thread_id": thread_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to create message")


@router.get("/threads/{thread_id}/messages/", response_model=List[Message])
def read_thread_messages(thread_id: int, db: Session = Depends(get_db)):
    try:
        messages = get_thread_messages(db, thread_id)
        logger.info(
            "Retrieved thread messages",
            extra={
                "thread_id": thread_id,
                "message_count": len(messages)
            }
        )
        return messages
    except Exception as e:
        logger.error(
            "Failed to get thread messages",
            extra={
                "error": str(e),
                "thread_id": thread_id
            }
        )
        raise HTTPException(status_code=500, detail="Failed to get thread messages") 