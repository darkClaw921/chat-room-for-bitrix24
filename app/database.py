from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import inspect

from .config import settings

# Проверяем URL базы данных и преобразуем в асинхронный URL если нужно
if settings.DATABASE_URL.startswith('sqlite'):
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace('sqlite://', 'sqlite+aiosqlite://', 1)
elif settings.DATABASE_URL.startswith('postgresql'):
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
else:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, echo=settings.DEBUG
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def create_tables():
    """
    Создание таблиц в базе данных если они не существуют
    """
    async with engine.begin() as conn:
        # Создаем таблицы напрямую, так как чаще всего они отсутствуют
        await conn.run_sync(Base.metadata.create_all)
        print("База данных инициализирована.")


async def get_db():
    """
    Dependency для получения сессии БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()