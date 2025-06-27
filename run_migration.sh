#!/bin/bash
# Скрипт для запуска миграции TelegramUser

echo "🚀 Запуск миграции для добавления новых полей в TelegramUser..."

# Проверка наличия uv
if command -v uv &> /dev/null; then
    echo "✅ Используется uv для запуска"
    uv run migration_add_telegram_user_fields.py
else
    echo "⚠️  uv не найден, используется python"
    # Активация виртуального окружения (если используется)
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Виртуальное окружение активировано"
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "✅ Виртуальное окружение активировано"
    fi
    
    # Запуск миграции
    python migration_add_telegram_user_fields.py
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Миграция успешно завершена!"
    echo "📝 Добавлены поля в TelegramUser:"
    echo "   - additional_info (TEXT) - Дополнительная информация"
    echo "   - deal_link (VARCHAR 500) - Ссылка на сделку"
    echo "   - apartments (VARCHAR 200) - Аппартаменты"
    echo ""
    echo "🔄 Обновленные файлы:"
    echo "   - app/models/user.py (модель TelegramUser)"
    echo "   - app/schemas/user.py (схемы Pydantic)"
else
    echo "❌ Ошибка при выполнении миграции"
    exit 1
fi 