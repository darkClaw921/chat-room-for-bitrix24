from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.message import Message
from app.crud import event as event_crud


async def process_events(
    db: AsyncSession, 
    event_type: str, 
    telegram_user_id: int,
    context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Обработка событий заданного типа
    
    Args:
        db: сессия базы данных
        event_type: тип события
        telegram_user_id: ID пользователя Telegram
        context: контекст события (сообщение и т.д.)
        
    Returns:
        Список действий для выполнения
    """
    # Получаем все активные события заданного типа
    events = await event_crud.get_active_events_by_type(
        db=db, 
        event_type=event_type,
        telegram_user_id=telegram_user_id
    )
    
    actions = []
    
    for event in events:
        # Проверяем условия срабатывания
        if await check_event_conditions(event, context):
            # Добавляем действие в список для выполнения
            action = {
                "event_id": event.id,
                "action_type": event.action_type,
                "action_data": event.action_data or {}
            }
            actions.append(action)
    
    return actions


async def check_event_conditions(event: Event, context: Dict[str, Any]) -> bool:
    """
    Проверка условий срабатывания события
    
    Args:
        event: событие для проверки
        context: контекст события
        
    Returns:
        True если все условия выполнены, иначе False
    """
    if not event.conditions:
        return True
    
    # Проверяем каждое условие
    for condition_key, condition_value in event.conditions.items():
        if condition_key == "text_contains":
            # Проверяем что сообщение содержит заданный текст
            if "message" not in context or not isinstance(context["message"], Message):
                return False
            
            message: Message = context["message"]
            if condition_value and condition_value.lower() not in message.text.lower():
                return False
                
        elif condition_key == "user_username":
            # Проверяем имя пользователя
            if "telegram_user" not in context:
                return False
                
            telegram_user = context["telegram_user"]
            if condition_value and telegram_user.username != condition_value:
                return False
    
    return True


async def execute_action(
    db: AsyncSession,
    action: Dict[str, Any],
    context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Выполнение действия
    
    Args:
        db: сессия базы данных
        action: действие для выполнения
        context: контекст события
        
    Returns:
        Результат выполнения действия
    """
    action_type = action.get("action_type")
    action_data = action.get("action_data", {})
    
    if action_type == "send_message":
        # Отправка сообщения
        chat_id = context.get("chat_id")
        text = action_data.get("text", "")
        
        if not chat_id or not text:
            return None
            
        return {
            "type": "send_message",
            "chat_id": chat_id,
            "text": text
        }
    
    elif action_type == "notify_manager":
        # Уведомление менеджера
        message = context.get("message")
        chat_id = context.get("chat_id")
        
        if not message or not chat_id:
            return None
            
        return {
            "type": "notify_manager",
            "chat_id": chat_id,
            "message_id": message.id
        }
    
    return None
 