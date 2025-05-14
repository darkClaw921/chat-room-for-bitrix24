from aiogram import Dispatcher

from .command import register_command_handlers
from .message import register_message_handlers


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрация всех обработчиков
    """
    register_command_handlers(dp)
    register_message_handlers(dp) 