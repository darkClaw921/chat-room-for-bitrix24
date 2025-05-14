from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .user import User, TelegramUser
from .message import Message


class ChatBase(BaseModel):
    telegram_user_id: int
    title: Optional[str] = None
    is_active: bool = True


class ChatCreate(ChatBase):
    manager_id: Optional[int] = None


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None
    manager_id: Optional[int] = None
    unread_count: Optional[int] = None


class ChatInDB(ChatBase):
    id: int
    manager_id: Optional[int] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Chat(ChatInDB):
    pass


class ChatWithRelations(Chat):
    telegram_user: Optional[TelegramUser] = None
    manager: Optional[User] = None
    messages: List[Message] = []


class ChatListItem(BaseModel):
    id: int
    title: Optional[str]
    telegram_user_id: int
    telegram_user: Optional[TelegramUser]
    unread_count: int
    last_message: Optional[Message]
    updated_at: datetime

    class Config:
        from_attributes = True 