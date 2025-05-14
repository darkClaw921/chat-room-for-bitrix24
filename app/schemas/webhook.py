from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union


class SendMessageRequest(BaseModel):
    """Схема для запроса отправки сообщения через webhook"""
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    text: str = Field(..., description="Текст сообщения для отправки")
    token: str = Field(..., description="Токен авторизации для защиты API")
    file: Optional[Dict[str, str]] = None  # {'name': 'filename.ext', 'data': 'base64string'}


class ClientMessageRequest(BaseModel):
    """Схема для запроса отправки сообщения от клиента через webhook"""
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    text: str = Field(..., description="Текст сообщения от клиента")
    token: str = Field(..., description="Токен авторизации для защиты API")
    username: Optional[str] = Field(None, description="Имя пользователя в Telegram (необязательно)")
    first_name: Optional[str] = Field(None, description="Имя клиента (необязательно)")
    last_name: Optional[str] = Field(None, description="Фамилия клиента (необязательно)")
    file: Optional[Dict[str, str]] = None  # {'name': 'filename.ext', 'data': 'base64string'}


class WebhookResponse(BaseModel):
    """Ответ на webhook запрос"""
    success: bool = Field(..., description="Статус выполнения операции")
    message: str = Field(..., description="Сообщение о результате")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные") 