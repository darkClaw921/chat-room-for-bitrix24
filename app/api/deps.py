from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_current_active_user, get_current_admin_user
from app.database import get_db
from app.models.user import User


# Зависимости для аутентификации
get_current_user_dependency = get_current_user
get_current_active_user_dependency = get_current_active_user
get_current_admin_user_dependency = get_current_admin_user


# Зависимость для получения сессии базы данных
async def get_db_dependency() -> Generator[AsyncSession, None, None]:
    """
    Получить сессию базы данных
    """
    async for db in get_db():
        yield db 