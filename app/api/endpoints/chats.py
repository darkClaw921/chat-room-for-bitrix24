from typing import Any, List, Dict, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import object_mapper

from app.api.deps import get_db_dependency, get_current_active_user_dependency
from app.models.user import User
from app.schemas.chat import Chat, ChatCreate, ChatUpdate, ChatWithRelations, ChatListItem, DashboardStatistics
from app.crud.chat import chat as crud_chat
from app.crud.message import message as crud_message


router = APIRouter()


def orm_to_dict(orm_object) -> Dict:
    """Преобразование ORM объекта в словарь для Pydantic V2"""
    if orm_object is None:
        return None
    
    result = {}
    for key in orm_object.__dict__:
        if not key.startswith('_'):
            value = getattr(orm_object, key)
            # Обрабатываем вложенные ORM объекты
            if hasattr(value, '__dict__') and not key.endswith('_id'):
                result[key] = orm_to_dict(value)
            else:
                result[key] = value
    return result


@router.get("/search/", response_model=List[ChatListItem])
async def search_chats(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Поиск чатов
    """
    chats = await crud_chat.search_chats(db=db, query=query)
    
    # Фильтруем чаты по доступу текущего пользователя
    filtered_chats = [chat for chat in chats if chat.manager_id == current_user.id]
    
    # Получаем последние сообщения для каждого чата
    result = []
    for chat in filtered_chats:
        last_message = await crud_message.get_last_message(db=db, chat_id=chat.id)
        
        # Преобразуем ORM объекты в словари для Pydantic V2
        chat_dict = {
            "id": chat.id,
            "title": chat.title,
            "telegram_user_id": chat.telegram_user_id,
            "telegram_user": orm_to_dict(chat.telegram_user) if chat.telegram_user else None,
            "unread_count": chat.unread_count,
            "last_message": orm_to_dict(last_message) if last_message else None,
            "updated_at": chat.updated_at
        }
        
        # Создаем объект Pydantic из словаря
        chat_item = ChatListItem.model_validate(chat_dict)
        result.append(chat_item)
    
    return result


@router.get("/", response_model=List[ChatListItem])
async def get_chats(
    skip: int = 0,
    limit: int = 10000,
    date_filter: Optional[str] = Query(None, description="Фильтр по дате: today, yesterday"),
    custom_date: Optional[date] = Query(None, description="Пользовательская дата для фильтра"),
    sort_by: str = Query("updated_at", description="Поле для сортировки: updated_at, last_message_date"),
    sort_order: str = Query("desc", description="Порядок сортировки: asc, desc"),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение списка чатов для текущего пользователя с фильтрацией и сортировкой
    """
    chats = await crud_chat.get_chats_by_manager(
        db=db, 
        manager_id=current_user.id, 
        skip=skip, 
        limit=limit,
        date_filter=date_filter,
        custom_date=custom_date,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Получаем последние сообщения для каждого чата
    result = []
    for chat in chats:
        last_message = await crud_message.get_last_message(db=db, chat_id=chat.id)
        
        # Преобразуем ORM объекты в словари для Pydantic V2
        chat_dict = {
            "id": chat.id,
            "title": chat.title,
            "telegram_user_id": chat.telegram_user_id,
            "telegram_user": orm_to_dict(chat.telegram_user) if chat.telegram_user else None,
            "unread_count": chat.unread_count,
            "last_message": orm_to_dict(last_message) if last_message else None,
            "updated_at": chat.updated_at
        }
        
        # Создаем объект Pydantic из словаря
        chat_item = ChatListItem.model_validate(chat_dict)
        result.append(chat_item)
    
    return result


@router.get("/{chat_id}", response_model=ChatWithRelations)
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение информации о чате по ID
    """
    chat = await crud_chat.get_chat_with_relations(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к чату
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому чату",
        )
    
    # Получаем сообщения
    messages = await crud_message.get_messages_by_chat(db=db, chat_id=chat.id)
    
    # Сбрасываем счетчик непрочитанных сообщений
    await crud_chat.reset_unread_count(db=db, chat_id=chat.id)
    
    # Отмечаем все сообщения как прочитанные
    await crud_message.mark_all_as_read(db=db, chat_id=chat.id)
    
    # Преобразуем ORM объекты в словари для Pydantic V2
    chat_dict = {
        "id": chat.id,
        "telegram_user_id": chat.telegram_user_id,
        "manager_id": chat.manager_id,
        "title": chat.title,
        "is_active": chat.is_active,
        "unread_count": 0,  # Сбрасываем счетчик
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "telegram_user": orm_to_dict(chat.telegram_user),
        "manager": orm_to_dict(chat.manager),
        "messages": [orm_to_dict(message) for message in messages]
    }
    
    # Создаем объект Pydantic из словаря
    result = ChatWithRelations.model_validate(chat_dict)
    
    return result


@router.post("/", response_model=Chat)
async def create_chat(
    chat_in: ChatCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Создание нового чата
    """
    # Добавляем текущего пользователя как менеджера
    chat_data = chat_in.model_dump()
    chat_data["manager_id"] = current_user.id
    
    chat = await crud_chat.create(db=db, obj_in=chat_in)
    return Chat.model_validate(orm_to_dict(chat))


@router.put("/{chat_id}", response_model=Chat)
async def update_chat(
    chat_id: int,
    chat_in: ChatUpdate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Обновление информации о чате
    """
    chat = await crud_chat.get(db=db, id=chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к чату
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому чату",
        )
    
    chat = await crud_chat.update(db=db, db_obj=chat, obj_in=chat_in)
    return Chat.model_validate(orm_to_dict(chat))


# Создаем отдельный роутер для статистики
stats_router = APIRouter()

@stats_router.get("/", response_model=DashboardStatistics)
async def get_dashboard_statistics(
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение статистики для дашборда
    """
    # Получаем статистику сообщений
    messages_stats = await crud_chat.get_messages_statistics(
        db=db, manager_id=current_user.id
    )
    
    # Получаем статистику диалогов
    chats_stats = await crud_chat.get_chats_statistics(
        db=db, manager_id=current_user.id
    )
    
    return DashboardStatistics(
        messages=messages_stats,
        chats=chats_stats
    ) 