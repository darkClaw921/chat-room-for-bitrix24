from aiogram import Dispatcher

from .db import DatabaseMiddleware


async def register_middlewares(dp: Dispatcher) -> None:
    """
    Регистрация middleware
    """
    # Регистрируем middleware для работы с базой данных
    dp.update.middleware(DatabaseMiddleware()) 