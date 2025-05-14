from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class Chat(BaseModel):
    """
    Модель чата между менеджером и клиентом
    """
    # Ключи
    manager_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    telegram_user_id = Column(Integer, ForeignKey('telegramuser.id'))
    
    # Атрибуты
    title = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Статус
    unread_count = Column(Integer, default=0)
    
    # Отношения
    manager = relationship("User", back_populates="chats")
    telegram_user = relationship("TelegramUser", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, telegram_user={self.telegram_user_id})>" 