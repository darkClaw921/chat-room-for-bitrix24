from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload

from app.models.chat import Chat
from app.schemas.chat import ChatCreate, ChatUpdate
from .base import CRUDBase


class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    async def get_by_telegram_user_id(
        self, db: AsyncSession, *, telegram_user_id: int
    ) -> Optional[Chat]:
        """
        Получить чат по ID пользователя Telegram
        """
        result = await db.execute(
            select(Chat).where(Chat.telegram_user_id == telegram_user_id)
        )
        return result.scalars().first()
        
    async def get_chats_by_manager(
        self, db: AsyncSession, *, manager_id: int, skip: int = 0, limit: int = 100
    ) -> List[Chat]:
        """
        Получить чаты по ID менеджера с предварительной загрузкой связанных объектов
        """
        result = await db.execute(
            select(Chat)
            .options(joinedload(Chat.telegram_user))
            .where(Chat.manager_id == manager_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
        
    async def get_chat_with_relations(
        self, db: AsyncSession, *, chat_id: int
    ) -> Optional[Chat]:
        """
        Получить чат со связанными объектами
        """
        result = await db.execute(
            select(Chat)
            .options(joinedload(Chat.telegram_user), joinedload(Chat.manager))
            .where(Chat.id == chat_id)
        )
        return result.unique().scalars().first()
        
    async def get_or_create_chat(
        self, db: AsyncSession, *, telegram_user_id: int, manager_id: Optional[int] = None
    ) -> Chat:
        """
        Получить или создать чат
        """
        chat = await self.get_by_telegram_user_id(db, telegram_user_id=telegram_user_id)
        
        if not chat:
            chat_data = {
                "telegram_user_id": telegram_user_id,
                "manager_id": manager_id,
                "is_active": True,
                "unread_count": 0
            }
            chat = Chat(**chat_data)
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
            
        return chat
        
    async def increment_unread_count(
        self, db: AsyncSession, *, chat_id: int
    ) -> Chat:
        """
        Увеличить счетчик непрочитанных сообщений
        """
        chat = await self.get(db, id=chat_id)
        if chat:
            chat.unread_count += 1
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
        return chat
        
    async def reset_unread_count(
        self, db: AsyncSession, *, chat_id: int
    ) -> Chat:
        """
        Сбросить счетчик непрочитанных сообщений
        """
        chat = await self.get(db, id=chat_id)
        if chat:
            chat.unread_count = 0
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
        return chat
        
    async def search_chats(
        self, db: AsyncSession, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Chat]:
        """
        Поиск чатов
        """
        result = await db.execute(
            select(Chat)
            .options(joinedload(Chat.telegram_user))
            .join(Chat.telegram_user)
            .where(
                or_(
                    Chat.title.ilike(f"%{query}%"),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


chat = CRUDChat(Chat) 