from sqlalchemy import Column, String, ForeignKey, Integer, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .base import BaseModel


class Message(BaseModel):
    """
    Модель сообщения
    """
    # Ключи
    chat_id = Column(Integer, ForeignKey('chat.id'))
    telegram_user_id = Column(Integer, ForeignKey('telegramuser.id'), nullable=True)
    manager_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    # Содержание сообщения
    text = Column(Text)
    message_type = Column(String(20), default="text")  # text, photo, document, etc.
    file_id = Column(String(255), nullable=True)  # ID файла в Telegram, если есть
    file_path = Column(String(255), nullable=True)  # Локальный путь к файлу, если есть
    
    # Статус сообщения
    is_read = Column(Boolean, default=False)
    is_from_manager = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Telegram-специфичная информация
    telegram_message_id = Column(Integer, nullable=True)
    
    # Отношения
    chat = relationship("Chat", back_populates="messages")
    telegram_user = relationship("TelegramUser", back_populates="messages")
    
    def mark_as_read(self):
        """
        Отметить сообщение как прочитанное
        """
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)
        
    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id})>" 