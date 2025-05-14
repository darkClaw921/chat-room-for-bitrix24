from typing import Optional, Union, BinaryIO
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

from app.config import settings
from .middleware import register_middlewares
from .handlers import register_handlers


# Инициализация бота и диспетчера
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def setup_bot() -> None:
    """
    Настройка бота
    """
    # Регистрация обработчиков
    register_handlers(dp)
    
    # Регистрация middleware
    await register_middlewares(dp)
    
    # Установка webhook если нужно
    if settings.WEBHOOK_URL:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != settings.WEBHOOK_URL:
            await bot.set_webhook(
                url=settings.WEBHOOK_URL,
                secret_token=settings.WEBHOOK_SECRET
            )
            logging.info(f"Webhook установлен на {settings.WEBHOOK_URL}")
    else:
        await bot.delete_webhook()
        logging.info("Webhook удален")


async def start_bot() -> None:
    """
    Запуск бота
    """
    await setup_bot()
    
    # Запускаем бота в режиме long polling если не используется webhook
    if not settings.WEBHOOK_URL:
        await dp.start_polling(bot)


async def stop_bot() -> None:
    """
    Остановка бота
    """
    await bot.session.close()
    await storage.close()


async def process_webhook_update(update_data: dict) -> None:
    """
    Обработка обновления через webhook
    """
    await dp.feed_update(bot, update_data)


# Функции для отправки сообщений
async def send_message(chat_id: int, text: str, **kwargs) -> None:
    """
    Отправка сообщения пользователю
    """
    await bot.send_message(chat_id=chat_id, text=text, **kwargs)


async def edit_message(chat_id: int, message_id: int, text: str, **kwargs) -> None:
    """
    Редактирование сообщения
    """
    await bot.edit_message_text(
        chat_id=chat_id, message_id=message_id, text=text, **kwargs
    )


async def send_document(chat_id: int, document: Union[str, BinaryIO], caption: Optional[str] = None, **kwargs) -> None:
    """
    Отправка файла пользователю
    
    Args:
        chat_id: ID чата
        document: Путь к файлу или файловый объект
        caption: Подпись к файлу (опционально)
    """
    # Проверяем, является ли document строкой с путем к файлу
    if isinstance(document, str):
        document = FSInputFile(document)
    # Если это файловый объект, нужно закрыть его после использования
    elif hasattr(document, 'name'):
        document = FSInputFile(document.name)
        
    await bot.send_document(
        chat_id=chat_id,
        document=document,
        caption=caption,
        **kwargs
    ) 