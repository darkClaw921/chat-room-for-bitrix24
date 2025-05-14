from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageBase(BaseModel):
    chat_id: int
    text: str
    message_type: str = "text"
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    is_from_manager: bool = False


class MessageCreate(MessageBase):
    telegram_user_id: Optional[int] = None
    manager_id: Optional[int] = None


class MessageUpdate(BaseModel):
    text: Optional[str] = None
    message_type: Optional[str] = None
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class MessageInDB(MessageBase):
    id: int
    telegram_user_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    telegram_message_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Message(MessageInDB):
    pass


class MessageOut(MessageInDB):
    """
    Сообщение для отправки на клиент
    """
    sender_name: Optional[str] = None 