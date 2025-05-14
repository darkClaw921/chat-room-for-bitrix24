from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets
from pathlib import Path


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
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None
    
    # Настройки API для внешних вызовов
    WEBHOOK_API_TOKEN: str = secrets.token_urlsafe(32)
    
    # CORS настройки
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings() 