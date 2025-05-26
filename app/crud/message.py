from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageUpdate
from .base import CRUDBase


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_messages_by_chat(
        self, db: AsyncSession, *, chat_id: int, skip: int = 0, limit: int = 100000
    ) -> List[Message]:
        """
        Получить сообщения по ID чата
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
        
    async def create_message(
        self, db: AsyncSession, *, obj_in: Dict[str, Any]
    ) -> Message:
        """
        Создать сообщение
        """
        db_obj = Message(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def mark_as_read(
        self, db: AsyncSession, *, message_id: int
    ) -> Optional[Message]:
        """
        Отметить сообщение как прочитанное
        """
        message = await self.get(db, id=message_id)
        if message:
            message.is_read = True
            message.read_at = datetime.now(timezone.utc)
            db.add(message)
            await db.commit()
            await db.refresh(message)
        return message
        
    async def mark_all_as_read(
        self, db: AsyncSession, *, chat_id: int
    ) -> None:
        """
        Отметить все сообщения в чате как прочитанные
        """
        messages = await self.get_messages_by_chat(db, chat_id=chat_id)
        for message in messages:
            if not message.is_read:
                message.is_read = True
                message.read_at = datetime.now(timezone.utc)
                db.add(message)
        
        await db.commit()
        
    async def get_unread_count(
        self, db: AsyncSession, *, chat_id: int
    ) -> int:
        """
        Получить количество непрочитанных сообщений
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id, Message.is_read == False)
        )
        return len(result.scalars().all())
        
    async def get_last_message(
        self, db: AsyncSession, *, chat_id: int
    ) -> Optional[Message]:
        """
        Получить последнее сообщение в чате
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        return result.scalars().first()


message = CRUDMessage(Message) 