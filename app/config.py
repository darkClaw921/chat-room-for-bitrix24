from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets
from pathlib import Path
import pytz
from datetime import timezone, timedelta


class Settings(BaseSettings):
    """
    Настройки приложения
    """
    # Базовые настройки приложения
    APP_NAME: str = "Чат-комната Bitrix24"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    
    # Директории проекта
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = Path(__file__).resolve().parent / "static"
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"
    
    # Настройки базы данных
    DATABASE_URL: str = "sqlite:///./app.db"
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin"
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None
    
    # Настройки API для внешних вызовов
    WEBHOOK_API_TOKEN: str = secrets.token_urlsafe(32)
    BITRIX_WEBHOOK:str='https://begt.bitrix24.ru/rest/1/1234567890/'
    DOMAIN_BITRIX:str='begt.bitrix24.ru'
    
    # Настройки времени и часового пояса
    TIMEZONE: str = "Asia/Yekaterinburg"  # UTC+5 по умолчанию
    # CORS настройки
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def tz(self) -> pytz.BaseTzInfo:
        """Получить объект часового пояса"""
        try:
            return pytz.timezone(self.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            # Если указан неверный часовой пояс, возвращаем UTC+5
            return pytz.timezone("Asia/Yekaterinburg")
    
    def get_local_time(self, utc_time=None):
        """Конвертировать UTC время в локальное время"""
        if utc_time is None:
            from datetime import datetime
            utc_time = datetime.utcnow()
        
        # Если время уже с timezone, конвертируем
        if utc_time.tzinfo is not None:
            return utc_time.astimezone(self.tz)
        else:
            # Если время naive (без timezone), предполагаем что это UTC
            utc_time = pytz.utc.localize(utc_time)
            return utc_time.astimezone(self.tz)


settings = Settings() 