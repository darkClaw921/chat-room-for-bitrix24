from fastapi import APIRouter

from app.api.endpoints import auth, chats, messages, events, webhook

api_router = APIRouter()

# Подключаем все маршруты
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"]) 