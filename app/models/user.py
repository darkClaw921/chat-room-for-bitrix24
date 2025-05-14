from sqlalchemy import Column, String, Boolean, Integer, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """
    Модель пользователя системы (менеджер)
    """
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Отношения
    chats = relationship("Chat", back_populates="manager")


class TelegramUser(BaseModel):
    """
    Модель пользователя Telegram (клиент)
    """
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(50), nullable=True)
    first_name = Column(String(50))
    last_name = Column(String(50), nullable=True)
    language_code = Column(String(10), nullable=True)
    
    # Дополнительная информация
    info = Column(Text, nullable=True)
    
    # Отношения
    chats = relationship("Chat", back_populates="telegram_user")
    messages = relationship("Message", back_populates="telegram_user") 