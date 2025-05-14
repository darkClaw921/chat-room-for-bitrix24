from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class Event(BaseModel):
    """
    Модель для настройки событий и автоматизации действий
    """
    # Основная информация
    name = Column(String(100))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Тип события
    event_type = Column(String(50))  # new_message, user_joined, keyword, etc.
    
    # Условия срабатывания
    conditions = Column(JSON, nullable=True)  # JSON с условиями
    
    # Действия
    action_type = Column(String(50))  # send_message, notify_manager, run_webhook, etc.
    action_data = Column(JSON, nullable=True)  # JSON с данными для действия
    
    # Связи
    manager_id = Column(Integer, ForeignKey('user.id'))
    telegram_user_id = Column(Integer, ForeignKey('telegramuser.id'), nullable=True)  # Если событие для конкретного пользователя
    
    def __repr__(self):
        return f"<Event(id={self.id}, name={self.name}, event_type={self.event_type})>" 