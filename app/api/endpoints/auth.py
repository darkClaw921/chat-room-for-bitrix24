from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency, get_current_active_user_dependency
from app.core.auth import authenticate_user
from app.core.security import create_access_token
from app.config import settings
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, Token


router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_dependency)
) -> Any:
    """
    Получение токена доступа по имени пользователя и паролю
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    # Устанавливаем токен в куки
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах
    response.set_cookie(
        key="token", 
        value=access_token, 
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,  # True в продакшене, False в разработке
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_active_user_dependency)
) -> Any:
    """
    Обновление токена доступа
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.username, expires_delta=access_token_expires
    )
    
    # Устанавливаем токен в куки
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах
    response.set_cookie(
        key="token", 
        value=access_token, 
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    """
    Выход из системы
    """
    # Очистка куки
    response.delete_cookie(
        key="token",
        path="/",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="lax"
    )
    return {"message": "Выход выполнен успешно"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.post("/register", response_model=UserSchema)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_dependency),
) -> Any:
    """
    Регистрация нового пользователя
    """
    from app.crud.user import user as crud_user
    
    # Проверяем, существует ли пользователь с таким именем
    user = await crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
    
    # Проверяем, существует ли пользователь с таким email
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
    # Создаем пользователя
    user = await crud_user.create(db, obj_in=user_in)
    
    return user