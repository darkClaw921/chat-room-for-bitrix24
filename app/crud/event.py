from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate
from .base import CRUDBase


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    async def get_by_manager(
        self, db: AsyncSession, *, manager_id: int, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        """
        Получить события по ID менеджера
        """
        result = await db.execute(
            select(Event)
            .where(Event.manager_id == manager_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
        
    async def get_active_events_by_type(
        self, db: AsyncSession, *, event_type: str, telegram_user_id: Optional[int] = None
    ) -> List[Event]:
        """
        Получить активные события по типу и опционально по ID пользователя Telegram
        """
        query = select(Event).where(Event.event_type == event_type, Event.is_active == True)
        
        # Если указан ID пользователя, то добавляем условие
        if telegram_user_id:
            query = query.where(
                or_(
                    Event.telegram_user_id == telegram_user_id,
                    Event.telegram_user_id == None
                )
            )
        
        result = await db.execute(query)
        return result.scalars().all()
        
    async def create_event(
        self, db: AsyncSession, *, obj_in: EventCreate
    ) -> Event:
        """
        Создать новое событие
        """
        event_data = obj_in.dict()
        db_obj = Event(**event_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def update_event(
        self, db: AsyncSession, *, db_obj: Event, obj_in: EventUpdate
    ) -> Event:
        """
        Обновить событие
        """
        update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def activate_event(
        self, db: AsyncSession, *, event_id: int
    ) -> Event:
        """
        Активировать событие
        """
        event = await self.get(db, id=event_id)
        if event:
            event.is_active = True
            db.add(event)
            await db.commit()
            await db.refresh(event)
        return event
        
    async def deactivate_event(
        self, db: AsyncSession, *, event_id: int
    ) -> Event:
        """
        Деактивировать событие
        """
        event = await self.get(db, id=event_id)
        if event:
            event.is_active = False
            db.add(event)
            await db.commit()
            await db.refresh(event)
        return event


event = CRUDEvent(Event) 