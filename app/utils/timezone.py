"""
Утилиты для работы с часовыми поясами
"""

from datetime import datetime
from typing import Optional
import pytz
from loguru import logger

from app.config import settings


def get_local_time(utc_time: Optional[datetime] = None) -> datetime:
    """
    Конвертировать UTC время в локальное время согласно настройкам приложения
    
    Args:
        utc_time: UTC время для конвертации. Если None, используется текущее время
        
    Returns:
        datetime: Время в локальном часовом поясе
    """
    if utc_time is None:
        utc_time = datetime.utcnow()
    
    try:
        # Если время уже с timezone, конвертируем
        if utc_time.tzinfo is not None:
            return utc_time.astimezone(settings.tz)
        else:
            # Если время naive (без timezone), предполагаем что это UTC
            utc_time = pytz.utc.localize(utc_time)
            return utc_time.astimezone(settings.tz)
    except Exception as e:
        logger.error(f"Ошибка при конвертации времени: {e}")
        return utc_time


def get_utc_time(local_time: Optional[datetime] = None) -> datetime:
    """
    Конвертировать локальное время в UTC
    
    Args:
        local_time: Локальное время для конвертации. Если None, используется текущее местное время
        
    Returns:
        datetime: Время в UTC
    """
    if local_time is None:
        local_time = datetime.now(settings.tz)
    
    try:
        # Если время уже с timezone, конвертируем в UTC
        if local_time.tzinfo is not None:
            return local_time.astimezone(pytz.utc)
        else:
            # Если время naive, предполагаем что это локальное время
            local_time = settings.tz.localize(local_time)
            return local_time.astimezone(pytz.utc)
    except Exception as e:
        logger.error(f"Ошибка при конвертации времени в UTC: {e}")
        return local_time


def format_local_time(utc_time: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Форматировать UTC время в строку в локальном часовом поясе
    
    Args:
        utc_time: UTC время для форматирования
        format_str: Формат строки
        
    Returns:
        str: Отформатированная строка времени
    """
    local_time = get_local_time(utc_time)
    return local_time.strftime(format_str)


def get_timezone_info() -> dict:
    """
    Получить информацию о текущем часовом поясе
    
    Returns:
        dict: Информация о часовом поясе
    """
    tz = settings.tz
    now_local = datetime.now(tz)
    now_utc = datetime.utcnow()
    
    return {
        "timezone": settings.TIMEZONE,
        "offset": str(now_local.utcoffset()),
        "name": tz.zone,
        "abbreviation": now_local.strftime("%Z"),
        "current_local_time": now_local.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "current_utc_time": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    } 