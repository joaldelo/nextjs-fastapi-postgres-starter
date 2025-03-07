from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

from app.models import User, Thread, Message
from app.schemas import ThreadCreate, MessageCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user(db: Session, user_id: int) -> Optional[User]:
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise


def get_user_by_name(db: Session, name: str) -> Optional[User]:
    try:
        return db.query(User).filter(User.name == name).first()
    except Exception as e:
        logger.error(f"Error getting user by name {name}: {str(e)}")
        raise


def get_thread(db: Session, thread_id: int) -> Optional[Thread]:
    try:
        return db.query(Thread).filter(Thread.id == thread_id).first()
    except Exception as e:
        logger.error(f"Error getting thread {thread_id}: {str(e)}")
        raise


def get_user_threads(db: Session, user_id: int) -> List[Thread]:
    try:
        return db.query(Thread).filter(Thread.user_id == user_id).all()
    except Exception as e:
        logger.error(f"Error getting threads for user {user_id}: {str(e)}")
        raise


def create_thread(db: Session, thread: ThreadCreate) -> Thread:
    try:
        db_thread = Thread(**thread.model_dump())
        db.add(db_thread)
        db.commit()
        db.refresh(db_thread)
        return db_thread
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        db.rollback()
        raise


def get_thread_messages(db: Session, thread_id: int) -> List[Message]:
    try:
        return db.query(Message).filter(Message.thread_id == thread_id).all()
    except Exception as e:
        logger.error(f"Error getting messages for thread {thread_id}: {str(e)}")
        raise


def create_message(db: Session, message: MessageCreate, thread_id: int) -> Message:
    try:
        db_message = Message(**message.model_dump(), thread_id=thread_id)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        db.rollback()
        raise 