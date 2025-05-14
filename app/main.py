import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse, RedirectResponse

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import create_tables, get_db
from app.api import api_router
from app.bot import start_bot, stop_bot, process_webhook_update
from app.core.auth import get_current_active_user


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Контекстный менеджер для запуска и остановки бота
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы в базе данных если их нет
    await create_tables()
    
    # Создаем директорию для загрузки файлов, если её нет
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    logger.info("Директория для загрузки файлов готова")
    
    # # Запускаем бота если не используется webhook
    # if not settings.WEBHOOK_URL:
    #     asyncio.create_task(start_bot())
    #     logger.info("Бот запущен в режиме long polling")
    # else:
    #     await start_bot()
    #     logger.info(f"Бот настроен на использование webhook: {settings.WEBHOOK_URL}")
    
    yield
    
    # # Останавливаем бота
    # await stop_bot()
    # logger.info("Бот остановлен")


# Создаем экземпляр FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Подключаем директорию с загружаемыми файлами
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Настройка шаблонов
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


# Маршруты для веб-интерфейса
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Главная страница
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": settings.APP_NAME}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Страница входа
    """
    # Проверяем, есть ли токен в куках
    token = request.cookies.get("token")
    if token:
        # Если токен есть, перенаправляем на страницу чатов
        return RedirectResponse(url="/chats")
    
    return templates.TemplateResponse(
        "auth/login.html", {"request": request, "title": "Вход в систему"}
    )


@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Страница со списком чатов
    """
    return templates.TemplateResponse(
        "chats/list.html", {"request": request, "title": "Чаты", "user": current_user}
    )


@app.get("/chats/{chat_id}", response_class=HTMLResponse)
async def chat_page(chat_id: int, request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Страница чата
    """
    from app.crud.chat import chat as crud_chat
    
    # Получаем информацию о чате
    chat = await crud_chat.get_chat_with_relations(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    
    # Проверяем доступ
    if chat.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому чату",
        )
    
    return templates.TemplateResponse(
        "chats/detail.html", 
        {
            "request": request, 
            "title": f"Чат с {chat.telegram_user.first_name}",
            "chat": chat,
            "user": current_user
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, current_user = Depends(get_current_active_user)):
    """
    Страница настроек
    """
    return templates.TemplateResponse(
        "settings/index.html", {"request": request, "title": "Настройки", "user": current_user}
    )


@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request, current_user = Depends(get_current_active_user)):
    """
    Страница настройки событий
    """
    return templates.TemplateResponse(
        "settings/events.html", {"request": request, "title": "События", "user": current_user}
    )


# Маршрут для обработки webhook от Telegram
@app.post(f"/webhook/{settings.TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    """
    Обработка webhook от Telegram
    """
    if settings.WEBHOOK_SECRET:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный токен",
            )
    
    update_data = await request.json()
    await process_webhook_update(update_data)
    
    return {"ok": True}


# Обработка ошибки 401 (Unauthorized)
@app.exception_handler(HTTPException)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Для XHR запросов возвращаем JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        # Для обычных запросов перенаправляем на страницу входа
        if not request.url.path.startswith("/api/"):
            if request.url.path != "/login":
                return RedirectResponse(url="/login", status_code=302)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Подключаем API маршруты
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.middleware("http")
async def jwt_cookie_middleware(request: Request, call_next):
    # Проверяем только для API запросов
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/auth/login"):
        # Если токен есть в cookie, добавляем его в заголовок Authorization
        if "token" in request.cookies:
            token = request.cookies.get("token")
            # Проверяем, нет ли уже заголовка авторизации
            if not any(h[0].lower() == b"authorization" for h in request.headers.__dict__["_list"]):
                request.headers.__dict__["_list"].append(
                    (b"authorization", f"Bearer {token}".encode())
                )
    
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    ) 