from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.crud.user import telegram_user as crud_telegram_user


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для работы с базой данных
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Создаем сессию базы данных
        async with SessionLocal() as db:
            # Добавляем сессию в данные
            data["db"] = db
            
            # Если есть пользователь, сохраняем его в базу
            if "event_from_user" in data:
                tg_user: TgUser = data["event_from_user"]
                
                # Создаем или обновляем пользователя в базе
                db_user = await crud_telegram_user.create_or_update(
                    db=db,
                    telegram_user={
                        "telegram_id": tg_user.id,
                        "username": tg_user.username,
                        "first_name": tg_user.first_name,
                        "last_name": tg_user.last_name,
                        "language_code": tg_user.language_code
                    }
                )
                
                # Добавляем пользователя из базы в данные
                data["db_user"] = db_user
            
            # Вызываем следующий обработчик
            return await handler(event, data) 