from aiogram import Dispatcher, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import TelegramUser
from app.crud.chat import chat as crud_chat
from app.crud.message import message as crud_message
from app.core.events import process_events, execute_action


async def handle_text_message(message: Message, db: AsyncSession, db_user: TelegramUser) -> None:
    """
    Обработчик текстовых сообщений
    """
    # Получаем или создаем чат
    chat = await crud_chat.get_or_create_chat(
        db=db, telegram_user_id=db_user.id
    )
    
    # Создаем сообщение в базе
    db_message = await crud_message.create_message(
        db=db,
        obj_in={
            "chat_id": chat.id,
            "telegram_user_id": db_user.id,
            "text": message.text,
            "message_type": "text",
            "is_from_manager": False,
            "telegram_message_id": message.message_id
        }
    )
    
    # Увеличиваем счетчик непрочитанных сообщений
    await crud_chat.increment_unread_count(db=db, chat_id=chat.id)
    
    # Обрабатываем события
    context = {
        "message": db_message,
        "telegram_user": db_user,
        "chat_id": chat.id
    }
    
    actions = await process_events(
        db=db,
        event_type="new_message",
        telegram_user_id=db_user.telegram_id,
        context=context
    )
    
    # Выполняем действия
    for action in actions:
        result = await execute_action(db=db, action=action, context=context)
        
        if result and result["type"] == "send_message":
            await message.answer(result["text"])


async def handle_photo_message(message: Message, db: AsyncSession, db_user: TelegramUser) -> None:
    """
    Обработчик сообщений с фото
    """
    # Получаем или создаем чат
    chat = await crud_chat.get_or_create_chat(
        db=db, telegram_user_id=db_user.id
    )
    
    # Получаем информацию о фото
    photo = message.photo[-1]  # Берем самое большое фото
    caption = message.caption or ""
    
    # Создаем сообщение в базе
    db_message = await crud_message.create_message(
        db=db,
        obj_in={
            "chat_id": chat.id,
            "telegram_user_id": db_user.id,
            "text": caption,
            "message_type": "photo",
            "file_id": photo.file_id,
            "is_from_manager": False,
            "telegram_message_id": message.message_id
        }
    )
    
    # Увеличиваем счетчик непрочитанных сообщений
    await crud_chat.increment_unread_count(db=db, chat_id=chat.id)
    
    # Отправляем подтверждение
    await message.answer("Фото получено и будет передано менеджеру.")


async def handle_document_message(message: Message, db: AsyncSession, db_user: TelegramUser) -> None:
    """
    Обработчик сообщений с документами
    """
    # Получаем или создаем чат
    chat = await crud_chat.get_or_create_chat(
        db=db, telegram_user_id=db_user.id
    )
    
    # Получаем информацию о документе
    document = message.document
    caption = message.caption or ""
    
    # Создаем сообщение в базе
    db_message = await crud_message.create_message(
        db=db,
        obj_in={
            "chat_id": chat.id,
            "telegram_user_id": db_user.id,
            "text": caption,
            "message_type": "document",
            "file_id": document.file_id,
            "is_from_manager": False,
            "telegram_message_id": message.message_id
        }
    )
    
    # Увеличиваем счетчик непрочитанных сообщений
    await crud_chat.increment_unread_count(db=db, chat_id=chat.id)
    
    # Отправляем подтверждение
    await message.answer("Документ получен и будет передан менеджеру.")


def register_message_handlers(dp: Dispatcher) -> None:
    """
    Регистрация обработчиков сообщений
    """
    dp.message.register(handle_text_message, F.text)
    dp.message.register(handle_photo_message, F.photo)
    dp.message.register(handle_document_message, F.document) 