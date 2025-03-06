from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    threads: Mapped[List["Thread"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


class Thread(Base):
    __tablename__ = "thread"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    user: Mapped["User"] = relationship(back_populates="threads")
    messages: Mapped[List["Message"]] = relationship(back_populates="thread", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Thread(id={self.id!r}, title={self.title!r}, user_id={self.user_id!r})"


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    thread_id: Mapped[int] = mapped_column(ForeignKey("thread.id"))
    
    thread: Mapped["Thread"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, role={self.role!r}, thread_id={self.thread_id!r})"
