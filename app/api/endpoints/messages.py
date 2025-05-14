from typing import Any, List
import base64
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency, get_current_active_user_dependency
from app.models.user import User
from app.schemas.message import Message, MessageCreate, MessageUpdate, MessageOut
from app.crud.message import message as crud_message
from app.crud.chat import chat as crud_chat
from app.bot.bot import send_message as bot_send_message
from app.bot.bot import send_document as bot_send_document


router = APIRouter()


@router.get("/{chat_id}", response_model=List[Message])
async def get_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение сообщений чата
    """
    # Проверяем доступ к чату
    chat = await crud_chat.get(db=db, id=chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому чату",
        )
    
    # Получаем сообщения
    messages = await crud_message.get_messages_by_chat(
        db=db, chat_id=chat_id, skip=skip, limit=limit
    )
    
    # Отмечаем сообщения как прочитанные
    await crud_message.mark_all_as_read(db=db, chat_id=chat_id)
    
    # Сбрасываем счетчик непрочитанных сообщений
    await crud_chat.reset_unread_count(db=db, chat_id=chat_id)
    
    return messages


async def save_file_from_base64(file_data: dict) -> str:
    """Сохраняет файл из base64 данных и возвращает имя файла"""
    if not file_data or 'name' not in file_data or 'data' not in file_data:
        return None
    
    # Создаем директорию uploads, если она не существует
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Генерируем уникальное имя файла
    filename = f"{uuid4()}_{file_data['name']}"
    file_path = upload_dir / filename
    
    # Декодируем и сохраняем файл
    try:
        file_content = base64.b64decode(file_data['data'])
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return None


@router.post("/", response_model=Message)
async def create_message(
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Создание нового сообщения
    """
    # Проверяем доступ к чату и загружаем связанные данные с telegram_user
    chat = await crud_chat.get_chat_with_relations(db=db, chat_id=message_in.chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому чату",
        )
    
    # Добавляем информацию о менеджере
    message_data = message_in.model_dump(exclude={"file"})
    message_data["manager_id"] = current_user.id
    message_data["is_from_manager"] = True
    
    # Обрабатываем файл, если он есть
    file_path = None
    if message_in.file:
        file_path = await save_file_from_base64(message_in.file)
        if file_path:
            message_data["message_type"] = "document"
            message_data["file_path"] = file_path
    
    # Создаем сообщение
    message = await crud_message.create_message(db=db, obj_in=message_data)
    
    # Отправляем сообщение в Telegram
    telegram_user = chat.telegram_user
    if telegram_user:
        # Если есть файл, отправляем его, иначе обычное сообщение
        if file_path and message_data["message_type"] == "document":
            background_tasks.add_task(
                bot_send_document,
                chat_id=telegram_user.telegram_id, 
                document=file_path, 
                caption=message.text if message.text else None
            )
        else:
            background_tasks.add_task(
                bot_send_message,
                chat_id=telegram_user.telegram_id,
                text=message.text
            )
    
    return message


@router.put("/{message_id}", response_model=Message)
async def update_message(
    message_id: int,
    message_in: MessageUpdate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Обновление сообщения
    """
    # Получаем сообщение
    message = await crud_message.get(db=db, id=message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено",
        )
    
    # Проверяем доступ к чату
    chat = await crud_chat.get(db=db, id=message.chat_id)
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому сообщению",
        )
    
    # Обновляем сообщение
    message = await crud_message.update(db=db, db_obj=message, obj_in=message_in)
    
    return message


@router.post("/{message_id}/read", response_model=Message)
async def mark_message_as_read(
    message_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Отметить сообщение как прочитанное
    """
    # Получаем сообщение
    message = await crud_message.get(db=db, id=message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено",
        )
    
    # Проверяем доступ к чату
    chat = await crud_chat.get(db=db, id=message.chat_id)
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому сообщению",
        )
    
    # Отмечаем сообщение как прочитанное
    message = await crud_message.mark_as_read(db=db, message_id=message_id)
    
    return message 