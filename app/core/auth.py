from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.config import settings
from app.database import get_db
from app.models import user as user_models
from app.schemas import user as user_schemas
from app.crud import user as user_crud
from .security import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> user_models.User:
    """
    Получить текущего авторизованного пользователя
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schemas.TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = await user_crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: user_models.User = Depends(get_current_user),
) -> user_models.User:
    """
    Получить текущего активного пользователя
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Неактивный пользователь"
        )
    return current_user


async def get_current_admin_user(
    current_user: user_models.User = Depends(get_current_active_user),
) -> user_models.User:
    """
    Получить текущего пользователя с правами администратора
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    return current_user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[user_models.User]:
    """
    Аутентификация пользователя по имени и паролю
    """
    user = await user_crud.get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user 