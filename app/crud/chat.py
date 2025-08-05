from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, asc, or_, and_, func, distinct
from sqlalchemy.orm import joinedload

from app.models.chat import Chat
from app.models.message import Message
from app.models.user import TelegramUser
from app.schemas.chat import ChatCreate, ChatUpdate
from .base import CRUDBase

logger = logging.getLogger(__name__)


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
        
    async def get_available_apartments(self, db: AsyncSession) -> List[str]:
        """
        Получить список всех доступных аппартаментов из базы данных
        """
        result = await db.execute(
            select(distinct(TelegramUser.apartments))
            .where(and_(
                TelegramUser.apartments.isnot(None),
                TelegramUser.apartments != ""
            ))
        )
        apartments = result.scalars().all()
        # Фильтруем пустые строки и возвращаем отсортированный список
        return sorted([apt for apt in apartments if apt and apt.strip()])

    async def get_chats_by_manager(
        self, 
        db: AsyncSession, 
        *, 
        manager_id: int, 
        skip: int = 0, 
        limit: int = 100,
        date_filter: Optional[str] = None,
        custom_date: Optional[date] = None,
        apartments_filter: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> List[Chat]:
        """
        Получить чаты по ID менеджера с предварительной загрузкой связанных объектов
        Поддерживает фильтрацию по дате, аппартаментам и сортировку
        """
        logger.info(f"Фильтры - date_filter: {date_filter}, custom_date: {custom_date}, apartments_filter: {apartments_filter}, sort_by: {sort_by}, sort_order: {sort_order}")
        
        # Базовый запрос
        query = (
            select(Chat)
            .options(joinedload(Chat.telegram_user))
            .where(Chat.manager_id == manager_id)
        )
        
        # Применяем фильтр по дате СООБЩЕНИЙ (не чатов)
        if date_filter or custom_date:
            target_date = None
            
            if custom_date:
                target_date = custom_date
                logger.info(f"Фильтр по пользовательской дате: {target_date}")
            elif date_filter == "today":
                target_date = date.today()
                logger.info(f"Фильтр за сегодня: {target_date}")
            elif date_filter == "yesterday":
                target_date = date.today() - timedelta(days=1)
                logger.info(f"Фильтр за вчера: {target_date}")
            else:
                logger.warning(f"Неизвестный фильтр по дате: {date_filter}")
                
            if target_date:
                start_date = datetime.combine(target_date, datetime.min.time())
                end_date = datetime.combine(target_date, datetime.max.time())
                
                # Фильтруем чаты, у которых есть сообщения в указанную дату
                date_filter_subquery = select(Message.chat_id).where(
                    and_(
                        Message.created_at >= start_date,
                        Message.created_at <= end_date
                    )
                ).distinct()
                
                query = query.where(Chat.id.in_(date_filter_subquery))
                logger.info(f"Применен фильтр по дате {target_date}")
        
        # Применяем фильтр по аппартаментам
        if apartments_filter:
            logger.info(f"Применяем фильтр по аппартаментам: {apartments_filter}")
            query = query.join(TelegramUser, Chat.telegram_user_id == TelegramUser.id)
            query = query.where(TelegramUser.apartments == apartments_filter)
        
        # Если сортировка по дате последнего сообщения - применяем SQL сортировку
        if sort_by == "last_message_date":
            logger.info("Сортировка по дате последнего сообщения через SQL")
            
            # Подзапрос для получения даты последнего сообщения
            last_message_subquery = (
                select(
                    Message.chat_id,
                    func.max(Message.created_at).label('last_message_date')
                )
                .group_by(Message.chat_id)
                .subquery()
            )
            
            # Присоединяем подзапрос к основному запросу
            query = query.outerjoin(
                last_message_subquery,
                Chat.id == last_message_subquery.c.chat_id
            )
            
            # Применяем сортировку
            if sort_order == "asc":
                query = query.order_by(asc(last_message_subquery.c.last_message_date))
            else:
                query = query.order_by(desc(last_message_subquery.c.last_message_date))
        else:
            logger.info("Сортировка по дате обновления чата")
            if sort_order == "asc":
                query = query.order_by(asc(Chat.updated_at))
            else:
                query = query.order_by(desc(Chat.updated_at))
        
        # Применяем пагинацию в конце
        query = query.offset(skip).limit(limit)
        
        logger.info(f"Выполняем SQL запрос")
        
        result = await db.execute(query)
        chats = result.unique().scalars().all()
        
        logger.info(f"Получено чатов: {len(chats)}")
        
        return chats
        
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
        
    async def get_messages_statistics(
        self, db: AsyncSession, *, manager_id: int
    ) -> Dict[str, int]:
        """
        Получить статистику новых сообщений для менеджера
        """
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Получаем чаты менеджера
        chats_result = await db.execute(
            select(Chat.id).where(Chat.manager_id == manager_id)
        )
        chat_ids = [row[0] for row in chats_result.fetchall()]
        
        if not chat_ids:
            return {"today": 0, "week": 0, "month": 0, "all_time": 0}
        
        # Статистика за сегодня
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == False,  # Сообщения от клиентов
                    Message.created_at >= today_start,
                    Message.created_at <= today_end
                )
            )
        )
        today_count = today_result.scalar() or 0
        
        # Статистика за неделю
        week_start = datetime.combine(week_ago, datetime.min.time())
        
        week_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == False,
                    Message.created_at >= week_start
                )
            )
        )
        week_count = week_result.scalar() or 0
        
        # Статистика за месяц
        month_start = datetime.combine(month_ago, datetime.min.time())
        
        month_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == False,
                    Message.created_at >= month_start
                )
            )
        )
        month_count = month_result.scalar() or 0
        
        # Статистика за все время
        all_time_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == False
                )
            )
        )
        all_time_count = all_time_result.scalar() or 0
        
        return {
            "today": today_count,
            "week": week_count,
            "month": month_count,
            "all_time": all_time_count
        }
        
    async def get_chats_statistics(
        self, db: AsyncSession, *, manager_id: int
    ) -> Dict[str, int]:
        """
        Получить статистику новых диалогов для менеджера
        """
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Статистика за сегодня
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_result = await db.execute(
            select(func.count(Chat.id))
            .where(
                and_(
                    Chat.manager_id == manager_id,
                    Chat.created_at >= today_start,
                    Chat.created_at <= today_end
                )
            )
        )
        today_count = today_result.scalar() or 0
        
        # Статистика за неделю
        week_start = datetime.combine(week_ago, datetime.min.time())
        
        week_result = await db.execute(
            select(func.count(Chat.id))
            .where(
                and_(
                    Chat.manager_id == manager_id,
                    Chat.created_at >= week_start
                )
            )
        )
        week_count = week_result.scalar() or 0
        
        # Статистика за месяц
        month_start = datetime.combine(month_ago, datetime.min.time())
        
        month_result = await db.execute(
            select(func.count(Chat.id))
            .where(
                and_(
                    Chat.manager_id == manager_id,
                    Chat.created_at >= month_start
                )
            )
        )
        month_count = month_result.scalar() or 0
        
        # Статистика за все время
        all_time_result = await db.execute(
            select(func.count(Chat.id))
            .where(Chat.manager_id == manager_id)
        )
        all_time_count = all_time_result.scalar() or 0
        
        return {
            "today": today_count,
            "week": week_count,
            "month": month_count,
            "all_time": all_time_count
        }
        
    async def get_instruction_requests_statistics(
        self, db: AsyncSession, *, manager_id: int
    ) -> Dict[str, int]:
        """
        Получить статистику запросов инструкций по заселению для менеджера
        """
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Получаем чаты менеджера
        chats_result = await db.execute(
            select(Chat.id).where(Chat.manager_id == manager_id)
        )
        chat_ids = [row[0] for row in chats_result.fetchall()]
        
        if not chat_ids:
            return {"today": 0, "week": 0, "month": 0, "all_time": 0}
        
        # Точный текст для поиска
        instruction_text = "🤖 Пользователь запросил 🗒 Инструкция по заселению"
        
        # Статистика за сегодня
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == True,  # Сообщения от менеджера
                    Message.text == instruction_text,
                    Message.created_at >= today_start,
                    Message.created_at <= today_end
                )
            )
        )
        today_count = today_result.scalar() or 0
        
        # Статистика за неделю
        week_start = datetime.combine(week_ago, datetime.min.time())
        
        week_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == True,
                    Message.text == instruction_text,
                    Message.created_at >= week_start
                )
            )
        )
        week_count = week_result.scalar() or 0
        
        # Статистика за месяц
        month_start = datetime.combine(month_ago, datetime.min.time())
        
        month_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == True,
                    Message.text == instruction_text,
                    Message.created_at >= month_start
                )
            )
        )
        month_count = month_result.scalar() or 0
        
        # Статистика за все время
        all_time_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.is_from_manager == True,
                    Message.text == instruction_text
                )
            )
        )
        all_time_count = all_time_result.scalar() or 0
        
        return {
            "today": today_count,
            "week": week_count,
            "month": month_count,
            "all_time": all_time_count
        }


chat = CRUDChat(Chat) 