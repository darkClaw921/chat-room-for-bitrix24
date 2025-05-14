from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency, get_current_active_user_dependency
from app.models.user import User
from app.schemas.event import Event, EventCreate, EventUpdate
from app.crud.event import event as crud_event


router = APIRouter()


@router.get("/", response_model=List[Event])
async def get_events(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение списка событий для текущего пользователя
    """
    events = await crud_event.get_by_manager(
        db=db, manager_id=current_user.id, skip=skip, limit=limit
    )
    return events


@router.get("/{event_id}", response_model=Event)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Получение информации о событии по ID
    """
    event = await crud_event.get(db=db, id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к событию
    if event.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому событию",
        )
    
    return event


@router.post("/", response_model=Event)
async def create_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Создание нового события
    """
    # Добавляем текущего пользователя как менеджера
    event_in_dict = event_in.dict()
    event_in_dict["manager_id"] = current_user.id
    
    # Создаем новый объект EventCreate с правильными данными
    from app.models.event import Event as EventModel
    db_obj = EventModel(**event_in_dict)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Обновление информации о событии
    """
    event = await crud_event.get(db=db, id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к событию
    if event.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому событию",
        )
    
    event = await crud_event.update_event(db=db, db_obj=event, obj_in=event_in)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> None:
    """
    Удаление события
    """
    event = await crud_event.get(db=db, id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к событию
    if event.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому событию",
        )
    
    await crud_event.remove(db=db, id=event_id)


@router.post("/{event_id}/activate", response_model=Event)
async def activate_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Активация события
    """
    event = await crud_event.get(db=db, id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к событию
    if event.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому событию",
        )
    
    event = await crud_event.activate_event(db=db, event_id=event_id)
    return event


@router.post("/{event_id}/deactivate", response_model=Event)
async def deactivate_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user_dependency),
) -> Any:
    """
    Деактивация события
    """
    event = await crud_event.get(db=db, id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )
    
    # Проверяем, что текущий пользователь имеет доступ к событию
    if event.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому событию",
        )
    
    event = await crud_event.deactivate_event(db=db, event_id=event_id)
    return event 