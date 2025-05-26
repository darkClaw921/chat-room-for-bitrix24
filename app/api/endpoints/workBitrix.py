from pprint import pprint
from fast_bitrix24 import BitrixAsync
from dotenv import load_dotenv
from dataclasses import dataclass
from app.config import settings
import asyncio
from typing import Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.message import Message as MessageModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Deal:
    telegram_id:str='UF_CRM_1747164098729'
    deal_id:str='ID'
    status:str='STAGE_ID'
    room_name: str='UF_CRM_ROOM_TYPE_NAME'
    ostatoc_payment:str='UF_CRM_1715183997779'
    file_payment:str='UF_CRM_1747158628163'
    chat_room:str='UF_CRM_1747245296634'
    class Status:
        guest_zaehal:str='C7:PREPARATION'
        guest_no_send_payment:str='C7:UC_3EBBY1'
        check_payment:str='C7:PREPAYMENT_INVOICE'
        prozivaet:str='C7:EXECUTING'

bit = BitrixAsync(settings.BITRIX_WEBHOOK, ssl=False)
domain=settings.DOMAIN_BITRIX

# Словарь для отслеживания сообщений, ожидающих проверки
pending_notifications: Dict[int, Dict[str, Any]] = {}

async def send_notification_to_bitrix(telegram_id:int):
    try:
        deal=await get_deal_by_telegram_id(telegram_id)
        
        message=f'новое сообщение от [URL=https://{domain}/crm/deal/details/{deal['ID']}/]{deal[Deal.room_name]}[/URL] -> [URL={deal[Deal.chat_room]}]ссылка на чат[/URL]'
        items={
            'USER_ID':deal['ASSIGNED_BY_ID'],
            'MESSAGE':message,
        }
        await bit.call('im.notify.personal.add',items=items)
        logger.info(f"Отправлено уведомление в Bitrix для telegram_id: {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")

async def check_message_read_status(message_id: int) -> bool:
    """
    Проверяет статус сообщения в базе данных
    
    Args:
        message_id: ID сообщения
    
    Returns:
        bool: True если сообщение прочитано, False если не прочитано
    """
    try:
        # Получаем соединение с базой данных
        db_generator = get_db()
        db = await anext(db_generator)
        try:
            # Запрос статуса сообщения
            query = select(MessageModel).where(MessageModel.id == message_id)
            result = await db.execute(query)
            message = result.scalars().first()
            
            if message:
                logger.info(f"Проверка статуса сообщения {message_id} в БД: is_read={message.is_read}")
                return message.is_read
            else:
                logger.warning(f"Сообщение {message_id} не найдено в базе данных")
                return False
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса сообщения {message_id}: {str(e)}")
        return False

async def schedule_notification(telegram_id: int, message_id: int, chat_id: int):
    """
    Планирует отправку уведомления через 10 секунд, если сообщение не прочитано
    
    Args:
        telegram_id: ID пользователя в телеграм
        message_id: ID сообщения
        chat_id: ID чата
    """
    logger.info(f"Планирование уведомления для message_id: {message_id}, telegram_id: {telegram_id}")
    
    # Сохраняем информацию о сообщении
    pending_notifications[message_id] = {
        "telegram_id": telegram_id,
        "chat_id": chat_id,
        "is_read": False
    }
    
    # Ждем 10 секунд
    await asyncio.sleep(10)
    
    # Проверяем, было ли сообщение прочитано в локальном словаре
    if message_id in pending_notifications:
        # Если в локальном словаре отмечено как прочитанное, то не отправляем
        if pending_notifications[message_id]["is_read"]:
            logger.info(f"Сообщение {message_id} уже отмечено как прочитанное, уведомление не отправляется")
        else:
            # Дополнительно проверяем статус в базе данных
            is_read_in_db = await check_message_read_status(message_id)
            
            if is_read_in_db:
                logger.info(f"Сообщение {message_id} прочитано согласно БД, уведомление не отправляется")
            else:
                # Если не прочитано ни в локальном словаре, ни в БД, отправляем уведомление
                logger.info(f"Сообщение {message_id} не прочитано, отправляем уведомление")
                await send_notification_to_bitrix(telegram_id)
        
        # Удаляем из словаря в любом случае
        del pending_notifications[message_id]

def mark_message_as_read(message_id: int):
    """
    Отмечает сообщение как прочитанное, чтобы не отправлять уведомление
    
    Args:
        message_id: ID сообщения
    """
    logger.info(f"Отметка сообщения {message_id} как прочитанного")
    
    if message_id in pending_notifications:
        logger.info(f"Сообщение {message_id} найдено в ожидающих, отмечаем как прочитанное")
        pending_notifications[message_id]["is_read"] = True
        return True
    else:
        logger.warning(f"Сообщение {message_id} не найдено в ожидающих уведомлениях")
        return False

async def get_deal_by_telegram_id(telegram_id:int):
    items={
        'filter':{
            Deal.telegram_id:telegram_id,
            'STAGE_SEMANTIC_ID':'P'
        },
        'select':['TITLE','ID','ASSIGNED_BY_ID','UF_CRM_1747164098729', Deal.room_name, Deal.chat_room],
        
    }
    # pprint(items)
    result=await bit.get_all('crm.deal.list',params=items)
    # pprint(result)
    return result[0]

async def main():
    # a=await is_deal_status(dealID=22215,status=Deal.Status.check_payment)
    # pprint(a)
    # contact=await find_contact_by_phone('79321213415')
    #https://apidocs.bitrix24.ru/api-reference/chats/messages/index.html
    # message='новое сообщение от[URL=https://beguest.bitrix24.ru/crm/deal/details/23115/]Апартаменты на 8 марта 204Д 16[/URL] [URL=http://31.129.103.113:8000/chats/1]ссылка на чат[/URL]'
    contact=await send_notification_to_bitrix(telegram_id=400923372)
    pprint(contact)