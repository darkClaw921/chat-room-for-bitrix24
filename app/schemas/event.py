from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class EventBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    event_type: str
    is_active: bool = True
    conditions: Optional[Dict[str, Any]] = None
    action_type: str
    action_data: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    manager_id: Optional[int] = None
    telegram_user_id: Optional[int] = None


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    event_type: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    telegram_user_id: Optional[int] = None


class EventInDB(EventBase):
    id: int
    manager_id: int
    telegram_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Event(EventInDB):
    pass 