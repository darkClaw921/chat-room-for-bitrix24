from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from sqlalchemy.future import select

from .config import settings
from .models.user import User
from .core.security import get_password_hash
from .models.base import Base

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


async def create_tables():
    """
    Создание таблиц в базе данных если они не существуют и создание администратора
    """
    async with engine.begin() as conn:
        # Создаем таблицы напрямую, так как чаще всего они отсутствуют
        await conn.run_sync(Base.metadata.create_all)
        print("База данных инициализирована.")
        
    # Добавление логики создания администратора
    async with SessionLocal() as db:
        # Проверяем, существует ли уже администратор
        admin_user = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        admin_user = admin_user.scalars().first()

        if not admin_user:
            # Создаем нового администратора
            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            new_admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True
            )
            db.add(new_admin)
            await db.commit()
            await db.refresh(new_admin)
            print(f"Пользователь администратор '{settings.ADMIN_USERNAME}' создан.")


async def get_db():
    """
    Dependency для получения сессии БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()