from typing import Any
import os
import base64
from pathlib import Path
from uuid import uuid4
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency
from app.config import settings
from app.schemas.webhook import SendMessageRequest, WebhookResponse, ClientMessageRequest
from app.bot.bot import send_message, send_document
from app.crud.user import telegram_user as crud_telegram_user, user as crud_user
from app.crud.chat import chat as crud_chat
from app.crud.message import message as crud_message
from app.api.endpoints.workBitrix import schedule_notification

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()


async def save_file_from_base64(file_data: dict) -> str:
    """Сохраняет файл из base64 данных и возвращает путь к файлу"""
    if not file_data or 'name' not in file_data or 'data' not in file_data:
        return None
    
    # Создаем директорию uploads, если она не существует
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Генерируем уникальное имя файла
    filename = f"{uuid4()}_{file_data['name']}"
    file_path = upload_dir / filename
    
    # Декодируем и сохраняем файл
    try:
        file_content = base64.b64decode(file_data['data'])
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return None


@router.post("/send-message", response_model=WebhookResponse)
async def send_message_webhook(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db_dependency),
) -> Any:
    """
    Отправка сообщения через webhook API.
    Позволяет отправлять сообщения клиентам через curl или другие HTTP клиенты.
    
    Если пользователя с указанным Telegram ID не существует, он будет создан автоматически.
    Если чата с указанным пользователем не существует, он будет создан автоматически.
    
    Поддерживает отправку файлов в формате base64:
    ```
    curl -X POST "http://localhost:8000/api/webhook/send-message" \
      -H "Content-Type: application/json" \
      -d '{"telegram_id": 123456789, "text": "Привет из API!", "token": "your-webhook-api-token", "file": {"name": "document.pdf", "data": "base64-encoded-content"}}'
    ```
    """
    # Проверяем токен для авторизации запроса
    if request.token != settings.WEBHOOK_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации",
        )
    
    try:
        # Проверяем существование пользователя Telegram или создаем нового
        telegram_user = await crud_telegram_user.get_by_telegram_id(db, telegram_id=request.telegram_id)
        
        if not telegram_user:
            # Создаем нового пользователя Telegram
            telegram_user_data = {
                "telegram_id": request.telegram_id,
                "username": f"user_{request.telegram_id}",  # Временное имя пользователя
                "first_name": f"User {request.telegram_id}",  # Временное имя
                "last_name": None,
                "language_code": "ru"
            }
            telegram_user = await crud_telegram_user.create_or_update(db, telegram_user=telegram_user_data)
        
        # Ищем менеджера-администратора для чата
        # Берем первого доступного менеджера (в реальном проекте нужна логика выбора)
        from sqlalchemy.future import select
        from app.models.user import User
        result = await db.execute(select(User).where(User.is_active == True).limit(1))
        manager = result.scalars().first()
        
        if not manager:
            return WebhookResponse(
                success=False,
                message="Нет доступных менеджеров в системе",
            )
        
        # Проверяем существование чата с пользователем или создаем новый
        chat = await crud_chat.get_or_create_chat(
            db, 
            telegram_user_id=telegram_user.id, 
            manager_id=manager.id
        )
        
        # Обрабатываем файл, если он есть
        file_path = None
        message_type = "text"
        
        if request.file:
            file_path = await save_file_from_base64(request.file)
            if file_path:
                message_type = "document"
        
        # Создаем запись о сообщении в базе данных
        message_data = {
            "chat_id": chat.id,
            "text": request.text,
            "is_from_manager": True,  # Сообщение от менеджера
            "manager_id": manager.id,
            "telegram_user_id": telegram_user.id,
            "message_type": message_type,
            "file_path": file_path
        }
        await crud_message.create_message(db, obj_in=message_data)
        
        # Отправляем сообщение или файл через Telegram бота
        if file_path and message_type == "document":
            await send_document(
                chat_id=request.telegram_id, 
                document=file_path, 
                caption=request.text if request.text else None
            )
        else:
            await send_message(chat_id=request.telegram_id, text=request.text)
        
        return WebhookResponse(
            success=True,
            message="Сообщение успешно отправлено",
            data={
                "telegram_id": request.telegram_id,
                "chat_id": chat.id,
                "file_path": file_path
            }
        )
    except Exception as e:
        # Обрабатываем возможные ошибки при отправке
        return WebhookResponse(
            success=False,
            message=f"Ошибка при отправке сообщения: {str(e)}",
        )


@router.post("/client-message", response_model=WebhookResponse)
async def client_message_webhook(
    request: ClientMessageRequest,
    db: AsyncSession = Depends(get_db_dependency),
) -> Any:
    """
    Получение сообщения от клиента через webhook API.
    Позволяет клиентам отправлять сообщения менеджерам через curl или другие HTTP клиенты.
    
    Если пользователя с указанным Telegram ID не существует, он будет создан автоматически.
    Если чата с указанным пользователем не существует, он будет создан автоматически.
    
    Автоматически обновляет профиль клиента новыми данными из запроса:
    - first_name, last_name, username - базовая информация
    - additional_info - дополнительная информация о клиенте
    - deal_link - ссылка на сделку в CRM
    - apartments - информация об аппартаментах
    
    Поддерживает отправку файлов в формате base64:
    ```
    curl -X POST "http://localhost:8000/api/webhook/client-message" \
      -H "Content-Type: application/json" \
      -d '{
        "telegram_id": 123456789, 
        "text": "Сообщение от клиента", 
        "token": "your-webhook-api-token", 
        "first_name": "Иван", 
        "last_name": "Иванов", 
        "username": "ivanov",
        "additional_info": "VIP клиент",
        "deal_link": "https://crm.example.com/deal/123",
        "apartments": "2-комнатная, 65м²",
        "file": {"name": "document.pdf", "data": "base64-encoded-content"}
      }'
    ```
    """
    # Проверяем токен для авторизации запроса
    if request.token != settings.WEBHOOK_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации",
        )
    
    try:
        # Проверяем существование пользователя Telegram или создаем/обновляем
        telegram_user = await crud_telegram_user.get_by_telegram_id(db, telegram_id=request.telegram_id)
        
        # Подготавливаем данные пользователя из запроса
        telegram_user_data = {
            "telegram_id": request.telegram_id,
            "username": request.username or (f"user_{request.telegram_id}" if not telegram_user else telegram_user.username),
            "first_name": request.first_name or (f"User {request.telegram_id}" if not telegram_user else telegram_user.first_name),
            "last_name": request.last_name if request.last_name is not None else (telegram_user.last_name if telegram_user else None),
            "additional_info": request.additional_info if request.additional_info is not None else (telegram_user.additional_info if telegram_user else None),
            "deal_link": request.deal_link if request.deal_link is not None else (telegram_user.deal_link if telegram_user else None),
            "apartments": request.apartments if request.apartments is not None else (telegram_user.apartments if telegram_user else None),
            "language_code": telegram_user.language_code if telegram_user else "ru"
        }
        
        if not telegram_user:
            # Создаем нового пользователя
            logger.info(f"Создаем нового пользователя с данными: {telegram_user_data}")
            telegram_user = await crud_telegram_user.create_or_update(db, telegram_user=telegram_user_data)
        else:
            # Обновляем существующего пользователя с новыми данными из запроса
            logger.info(f"Обновляем пользователя {telegram_user.id} с данными: {telegram_user_data}")
            telegram_user = await crud_telegram_user.create_or_update(db, telegram_user=telegram_user_data)
        
        # Ищем менеджера-администратора для чата
        # Берем первого доступного менеджера
        from sqlalchemy.future import select
        from app.models.user import User
        result = await db.execute(select(User).where(User.is_active == True).limit(1))
        manager = result.scalars().first()
        
        if not manager:
            return WebhookResponse(
                success=False,
                message="Нет доступных менеджеров в системе",
            )
        
        # Получаем или создаем чат
        chat = await crud_chat.get_or_create_chat(
            db, 
            telegram_user_id=telegram_user.id, 
            manager_id=manager.id
        )
        
        # Обрабатываем файл, если он есть
        file_path = None
        message_type = "text"
        
        if request.file:
            file_path = await save_file_from_base64(request.file)
            if file_path:
                message_type = "document"
        
        # Создаем запись о сообщении в базе данных
        message_data = {
            "chat_id": chat.id,
            "text": request.text,
            "is_from_manager": False,  # Сообщение от клиента
            "telegram_user_id": telegram_user.id,
            "message_type": message_type,
            "file_path": file_path
        }
        message = await crud_message.create_message(db, obj_in=message_data)
        
        # Увеличиваем счетчик непрочитанных сообщений
        await crud_chat.increment_unread_count(db, chat_id=chat.id)
        
        # Планируем отправку уведомления, если сообщение не будет прочитано через 10 секунд
        logger.info(f"Планирование уведомления из webhook для telegram_id: {request.telegram_id}, message_id: {message.id}")
        asyncio.create_task(schedule_notification(
            telegram_id=request.telegram_id,
            message_id=message.id,
            chat_id=chat.id
        ))
        
        return WebhookResponse(
            success=True,
            message="Сообщение от клиента принято",
            data={
                "telegram_id": request.telegram_id,
                "chat_id": chat.id,
                "message_id": message.id,
                "file_path": file_path
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от клиента: {str(e)}")
        # Обрабатываем возможные ошибки
        return WebhookResponse(
            success=False,
            message=f"Ошибка при обработке сообщения: {str(e)}",
        ) 