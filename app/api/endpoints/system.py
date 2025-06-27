from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency, get_current_active_user_dependency
from app.models.user import User
from app.utils.timezone import get_timezone_info
from app.config import settings

router = APIRouter()


@router.get("/timezone")
async def get_timezone_information(
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение информации о часовом поясе системы
    """
    return get_timezone_info()


@router.get("/time")
async def get_current_time(
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение текущего времени в локальном часовом поясе
    """
    from app.utils.timezone import get_local_time, format_local_time
    from datetime import datetime
    
    utc_now = datetime.utcnow()
    local_now = get_local_time(utc_now)
    
    return {
        "utc_time": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "local_time": local_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "formatted_local": format_local_time(utc_now),
        "timezone": settings.TIMEZONE
    } 