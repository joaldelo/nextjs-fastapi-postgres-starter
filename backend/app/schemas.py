from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MessageBase(BaseModel):
    content: str
    role: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    created_at: datetime
    thread_id: int

    class Config:
        from_attributes = True


class ThreadBase(BaseModel):
    title: str


class ThreadCreate(ThreadBase):
    user_id: int


class Thread(ThreadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    messages: List[Message] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str



class User(UserBase):
    id: int
    threads: List[Thread] = []

    class Config:
        from_attributes = True 