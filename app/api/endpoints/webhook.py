from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency
from app.config import settings
from app.schemas.webhook import SendMessageRequest, WebhookResponse, ClientMessageRequest
from app.bot.bot import send_message
from app.crud.user import telegram_user as crud_telegram_user, user as crud_user
from app.crud.chat import chat as crud_chat
from app.crud.message import message as crud_message


router = APIRouter()


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
    
    Пример использования с curl:
    ```
    curl -X POST "http://localhost:8000/api/webhook/send-message" \
      -H "Content-Type: application/json" \
      -d '{"telegram_id": 123456789, "text": "Привет из API!", "token": "your-webhook-api-token"}'
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
        
        # Создаем запись о сообщении в базе данных
        message_data = {
            "chat_id": chat.id,
            "text": request.text,
            "is_from_manager": True,  # Сообщение от менеджера
            "manager_id": manager.id,
            "telegram_user_id": telegram_user.id,
            "message_type": "text"
        }
        await crud_message.create_message(db, obj_in=message_data)
        
        # Отправляем сообщение через Telegram бота
        await send_message(chat_id=request.telegram_id, text=request.text)
        
        return WebhookResponse(
            success=True,
            message="Сообщение успешно отправлено",
            data={
                "telegram_id": request.telegram_id,
                "chat_id": chat.id
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
    
    Пример использования с curl:
    ```
    curl -X POST "http://localhost:8000/api/webhook/client-message" \
      -H "Content-Type: application/json" \
      -d '{"telegram_id": 123456789, "text": "Сообщение от клиента", "token": "your-webhook-api-token", "first_name": "Иван", "last_name": "Иванов", "username": "ivanov"}'
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
            # Создаем нового пользователя Telegram с данными из запроса или значениями по умолчанию
            telegram_user_data = {
                "telegram_id": request.telegram_id,
                "username": request.username or f"user_{request.telegram_id}",
                "first_name": request.first_name or f"User {request.telegram_id}",
                "last_name": request.last_name,
                "language_code": "ru"
            }
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
        
        # Создаем запись о сообщении в базе данных
        message_data = {
            "chat_id": chat.id,
            "text": request.text,
            "is_from_manager": False,  # Сообщение от клиента
            "telegram_user_id": telegram_user.id,
            "message_type": "text"
        }
        message = await crud_message.create_message(db, obj_in=message_data)
        
        # Увеличиваем счетчик непрочитанных сообщений
        await crud_chat.increment_unread_count(db, chat_id=chat.id)
        
        return WebhookResponse(
            success=True,
            message="Сообщение от клиента принято",
            data={
                "telegram_id": request.telegram_id,
                "chat_id": chat.id,
                "message_id": message.id
            }
        )
    except Exception as e:
        # Обрабатываем возможные ошибки
        return WebhookResponse(
            success=False,
            message=f"Ошибка при обработке сообщения: {str(e)}",
        ) 