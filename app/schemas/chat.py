from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

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


# Новые схемы для фильтрации и статистики

class ChatFilters(BaseModel):
    """Схема для параметров фильтрации чатов"""
    date_filter: Optional[str] = Field(None, description="Фильтр по дате: today, yesterday")
    custom_date: Optional[date] = Field(None, description="Пользовательская дата для фильтра")
    sort_by: str = Field("updated_at", description="Поле для сортировки: updated_at, last_message_date")
    sort_order: str = Field("desc", description="Порядок сортировки: asc, desc")


class Statistics(BaseModel):
    """Схема для статистики"""
    today: int = Field(0, description="Количество за сегодня")
    week: int = Field(0, description="Количество за неделю")
    month: int = Field(0, description="Количество за месяц")
    all_time: int = Field(0, description="Количество за все время")
    instruction_requests: Optional["Statistics"] = Field(None, description="Статистика запросов инструкций по заселению")


class DashboardStatistics(BaseModel):
    """Схема для статистики дашборда"""
    messages: Statistics = Field(description="Статистика сообщений")
    chats: Statistics = Field(description="Статистика диалогов")
    instruction_requests: Statistics = Field(description="Статистика запросов инструкций по заселению") 