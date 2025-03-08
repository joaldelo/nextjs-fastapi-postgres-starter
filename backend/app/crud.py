from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging

from app.models import User, Thread, Message
from app.schemas import ThreadCreate, MessageCreate
from app.core.logging import logger


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    try:
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.threads).selectinload(Thread.messages)
            )
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error("Error getting user", extra={"user_id": user_id, "error": str(e)})
        raise


async def get_user_by_name(db: AsyncSession, name: str) -> Optional[User]:
    """Get a user by name."""
    try:
        result = await db.execute(
            select(User)
            .where(User.name == name)
            .options(
                selectinload(User.threads).selectinload(Thread.messages)
            )
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error("Error getting user by name", extra={"name": name, "error": str(e)})
        raise


async def get_thread(db: AsyncSession, thread_id: int) -> Optional[Thread]:
    """Get a thread by ID."""
    try:
        # Log the session state
        logger.info(
            "Database session state",
            extra={
                "thread_id": thread_id,
                "session_active": db.is_active,
                "session_id": id(db)
            }
        )

        # Execute the query
        result = await db.execute(
            select(Thread)
            .where(Thread.id == thread_id)
            .options(
                selectinload(Thread.messages),
                selectinload(Thread.user)
            )
        )
        
        # Get the thread
        thread = result.scalar_one_or_none()
        
        if thread is None:
            logger.warning(
                "Thread not found",
                extra={
                    "thread_id": thread_id,
                    "error": "Thread does not exist in database"
                }
            )
            return None
            
        return thread
        
    except Exception as e:
        # Get detailed error information
        error_info = {
            "thread_id": thread_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": repr(e),
            "session_active": getattr(db, 'is_active', None),
            "session_id": id(db)
        }
        
        logger.error(
            "Database error while getting thread",
            extra=error_info
        )
        # Return None instead of raising to handle gracefully
        return None


async def get_user_threads(db: AsyncSession, user_id: int) -> List[Thread]:
    """Get all threads for a user."""
    try:
        result = await db.execute(
            select(Thread)
            .where(Thread.user_id == user_id)
            .options(
                selectinload(Thread.messages),
                selectinload(Thread.user)
            )
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error("Error getting user threads", extra={"user_id": user_id, "error": str(e)})
        raise


async def create_thread(db: AsyncSession, thread: ThreadCreate) -> Thread:
    """Create a new thread."""
    try:
        db_thread = Thread(**thread.model_dump())
        db.add(db_thread)
        await db.commit()
        await db.refresh(db_thread)
        
        # Reload the thread with relationships
        result = await db.execute(
            select(Thread)
            .where(Thread.id == db_thread.id)
            .options(
                selectinload(Thread.messages),
                selectinload(Thread.user)
            )
        )
        return result.scalar_one()
    except Exception as e:
        logger.error("Error creating thread", extra={"error": str(e)})
        await db.rollback()
        raise


async def get_thread_messages(db: AsyncSession, thread_id: int) -> List[Message]:
    """Get all messages for a thread."""
    try:
        result = await db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .options(selectinload(Message.thread))
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error("Error getting thread messages", extra={"thread_id": thread_id, "error": str(e)})
        raise


async def create_message(db: AsyncSession, message: MessageCreate, thread_id: int) -> Message:
    """Create a new message in a thread."""
    try:
        db_message = Message(**message.model_dump(), thread_id=thread_id)
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        
        # Reload the message with relationships
        result = await db.execute(
            select(Message)
            .where(Message.id == db_message.id)
            .options(selectinload(Message.thread))
        )
        return result.scalar_one()
    except Exception as e:
        logger.error("Error creating message", extra={
            "thread_id": thread_id,
            "error": str(e)
        })
        await db.rollback()
        raise 