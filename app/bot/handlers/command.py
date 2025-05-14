from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import TelegramUser
from app.crud.chat import chat as crud_chat


async def cmd_start(message: Message, db: AsyncSession, db_user: TelegramUser) -> None:
    """
    Обработчик команды /start
    """
    # Создаем или получаем чат
    chat = await crud_chat.get_or_create_chat(
        db=db, telegram_user_id=db_user.id
    )
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Это чат для связи с менеджером. Напишите ваш вопрос, и менеджер ответит вам в ближайшее время."
    )


async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help
    """
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать общение\n"
        "/help - Показать эту справку"
    )


def register_command_handlers(dp: Dispatcher) -> None:
    """
    Регистрация обработчиков команд
    """
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help")) 