#!/usr/bin/env python3
"""
Миграция для добавления новых полей в TelegramUser:
- additional_info (Дополнительная информация)
- deal_link (Ссылка на сделку) 
- apartments (Аппартаменты)
"""

import asyncio
from loguru import logger
from sqlalchemy import text
from app.database import engine

async def check_column_exists(connection, table_name, column_name):
    """Проверяет существование колонки в таблице"""
    try:
        result = await connection.execute(text(f"PRAGMA table_info({table_name})"))
        columns = result.fetchall()
        return any(column[1] == column_name for column in columns)
    except Exception:
        return False

async def run_migration():
    """Запуск миграции для добавления новых полей в TelegramUser"""
    
    logger.info("Начинаю миграцию: добавление полей в TelegramUser")
    
    # Список новых полей для добавления
    new_columns = [
        ("additional_info", "TEXT"),
        ("deal_link", "VARCHAR(500)"),
        ("apartments", "VARCHAR(200)")
    ]
    
    try:
        async with engine.begin() as connection:
            for column_name, column_type in new_columns:
                # Проверяем существование колонки
                exists = await check_column_exists(connection, "telegramuser", column_name)
                
                if not exists:
                    command = f"ALTER TABLE telegramuser ADD COLUMN {column_name} {column_type};"
                    logger.info(f"Добавляю колонку: {column_name} ({column_type})")
                    await connection.execute(text(command))
                else:
                    logger.info(f"Колонка {column_name} уже существует, пропускаю")
                
        logger.success("Миграция успешно завершена!")
        logger.info("Добавленные поля:")
        logger.info("- additional_info (TEXT) - Дополнительная информация")
        logger.info("- deal_link (VARCHAR 500) - Ссылка на сделку")
        logger.info("- apartments (VARCHAR 200) - Аппартаменты")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении миграции: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(run_migration()) 