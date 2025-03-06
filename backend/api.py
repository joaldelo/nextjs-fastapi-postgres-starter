from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from db_engine import get_db
from models import User, Thread, Message
from schemas import  User, ThreadCreate, Thread, MessageCreate, Message
from crud import (
    get_user, get_user_threads,
    get_thread, create_thread, get_thread_messages,
    create_message
)
from chatbot import SimpleChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
chatbot = SimpleChatbot()


 

@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = get_user(db, user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.post("/threads/", response_model=Thread)
def create_new_thread(thread: ThreadCreate, db: Session = Depends(get_db)):
    try:
        db_thread = create_thread(db, thread)
        logger.info(f"Created new thread: {db_thread.title}")
        return db_thread
    except Exception as e:
        logger.error(f"Failed to create thread: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create thread")


@router.get("/threads/{thread_id}", response_model=Thread)
def read_thread(thread_id: int, db: Session = Depends(get_db)):
    try:
        db_thread = get_thread(db, thread_id)
        if db_thread is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return db_thread
    except Exception as e:
        logger.error(f"Failed to get thread {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get thread")


@router.get("/users/{user_id}/threads/", response_model=List[Thread])
def read_user_threads(user_id: int, db: Session = Depends(get_db)):
    try:
        threads = get_user_threads(db, user_id)
        return threads
    except Exception as e:
        logger.error(f"Failed to get threads for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user threads")


@router.post("/threads/{thread_id}/messages/", response_model=Message)
def create_new_message(thread_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    try:
        # Verify thread exists
        db_thread = get_thread(db, thread_id)
        if db_thread is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Create user message
        db_message = create_message(db, message, thread_id)
        logger.info(f"Created new user message in thread {thread_id}")
        
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
        logger.info(f"Created bot response in thread {thread_id}")
        
        return db_message
    except Exception as e:
        logger.error(f"Failed to create message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create message")


@router.get("/threads/{thread_id}/messages/", response_model=List[Message])
def read_thread_messages(thread_id: int, db: Session = Depends(get_db)):
    try:
        messages = get_thread_messages(db, thread_id)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages for thread {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get thread messages") 