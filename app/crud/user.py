from typing import Any, Dict, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password
from app.models.user import User, TelegramUser
from app.schemas.user import UserCreate, UserUpdate, TelegramUserCreate, TelegramUserUpdate
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        Получить пользователя по имени пользователя
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()
        
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Получить пользователя по email
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
        
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Создать нового пользователя
        """
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Обновить пользователя
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
            
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
        
    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[User]:
        """
        Аутентификация пользователя
        """
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
        
    async def is_active(self, user: User) -> bool:
        """
        Проверить, активен ли пользователь
        """
        return user.is_active
        
    async def is_admin(self, user: User) -> bool:
        """
        Проверить, является ли пользователь администратором
        """
        return user.is_admin
        

class CRUDTelegramUser(CRUDBase[TelegramUser, TelegramUserCreate, TelegramUserUpdate]):
    async def get_by_telegram_id(
        self, db: AsyncSession, *, telegram_id: int
    ) -> Optional[TelegramUser]:
        """
        Получить пользователя Telegram по telegram_id
        """
        result = await db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalars().first()
        
    async def create_or_update(
        self, db: AsyncSession, *, telegram_user: Dict[str, Any]
    ) -> TelegramUser:
        """
        Создать или обновить пользователя Telegram
        """
        db_user = await self.get_by_telegram_id(db, telegram_id=telegram_user["telegram_id"])
        
        if db_user:
            # Обновляем существующего пользователя
            for field, value in telegram_user.items():
                setattr(db_user, field, value)
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        else:
            # Создаем нового пользователя
            db_obj = TelegramUser(**telegram_user)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj


user = CRUDUser(User)
telegram_user = CRUDTelegramUser(TelegramUser)


# Функции-хелперы
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    return await user.get_by_username(db, username=username) 