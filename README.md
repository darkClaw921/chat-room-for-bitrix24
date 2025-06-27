# Чат-комната для Bitrix24

Система для общения менеджеров с клиентами через Telegram. Менеджеры отвечают от лица бота, а клиенты общаются через свой Telegram аккаунт.

## Особенности

- Авторизация менеджеров с сохранением сессии
- Хранение истории сообщений в базе данных
- Отображение чатов на веб-странице
- Уникальный идентификатор для каждой страницы чата на основе ID пользователя
- Настройка автоматизации событий (например, автоматические ответы на определенные сообщения)
- Поддержка светлой и темной темы (Bootstrap)

## Технологический стек

- **Backend**: Python, FastAPI
- **База данных**: SQLAlchemy (поддержка MySQL и PostgreSQL)
- **Telegram Bot**: aiogram 3.x
- **Frontend**: Bootstrap 5 (светлая и темная тема)

## Установка и запуск

### Предварительные требования

- Python 3.9 или выше
- Poetry (менеджер пакетов)
- MySQL или PostgreSQL (опционально, по умолчанию используется SQLite)

### Установка зависимостей

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/chat-room-for-bitrix24.git
cd chat-room-for-bitrix24

# Установка зависимостей
uv sync
```

### Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте файл `.env` и укажите необходимые параметры:

```
# Базовые настройки
APP_NAME="Чат-комната Bitrix24"
DEBUG=True
SECRET_KEY=your_secret_key_here

# База данных
DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=postgresql://user:password@localhost/chat_room

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# WEBHOOK_URL=https://your-domain.com/webhook/your_telegram_bot_token_here
# WEBHOOK_SECRET=your_webhook_secret_here
```

### Запуск приложения

```bash
uv run -m app.main
```

Приложение будет доступно по адресу http://localhost:8000

## Структура проекта

```
chat-room-for-bitrix24/
├── app/
│   ├── api/                    # API роуты
│   ├── bot/                    # Telegram бот
│   ├── core/                   # Основные компоненты
│   ├── crud/                   # CRUD операции
│   ├── models/                 # SQLAlchemy модели
│   ├── schemas/                # Pydantic схемы
│   ├── static/                 # Статические файлы
│   ├── templates/              # Шаблоны Jinja2
│   ├── __init__.py
│   ├── config.py               # Конфигурация приложения
│   ├── database.py             # Настройка подключения к БД
│   └── main.py                 # Основная точка входа
├── .env                        # Переменные окружения
├── .env.example                # Пример переменных окружения
├── pyproject.toml              # Зависимости проекта
└── README.md                   # Документация
```

## Создание первого пользователя

Для создания первого пользователя (менеджера) используйте API:

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "email": "admin@example.com", "password": "admin123", "is_active": true}'
```

После этого вы сможете войти в систему через веб-интерфейс.


Отправка сообщения в чат пользователю
```bash
curl -X POST "http://localhost:8000/api/webhook/send-message" \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 400923372, "text": "Привет из API!", "token": "your-secret-api-token-here"}'
```

Отправляет сообщение менеджеру в чат на сайте
```bash
curl -X POST "http://localhost:8000/api/webhook/client-message" \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 400923372, "text": "Привет из API!", "token": "your-secret-api-token-here"}'
```

# Пример отправки сообщения в чат пользователю через робота битрикса на основе yandex function
https://functions.yandexcloud.net/d4eipaa2sh28tm87hbp?user_id={{id telegram user}}

```python
from pprint import pprint
import json
import base64
import requests
import os


IP_CHAT_ROOM=os.getenv('IP_CHAT_ROOM')
WEBHOOK_API_TOKEN=os.getenv('WEBHOOK_API_TOKEN')

def send_message_to_client(telegram_id, text):
    """Отправляет сообщение пользователю в телеграмм"""
    url=f'http://{IP_CHAT_ROOM}/api/webhook/send-message'
    data={
        'telegram_id': telegram_id,
        'text': text,
        'token': WEBHOOK_API_TOKEN
    }
    # print(data)
    response= requests.post(url, json=data)
    # pprint(response)
    return response.json()

def handler(event, context):
    # pprint(event)

    body=event['body']
    user_id=event['queryStringParameters']['user_id']
    print(f'{user_id}')
    send_message_to_client(user_id,"""Спасибо! Ваш платеж подтвержден. 
Для доступа к информации по проживанию нажмите на /info""")
    #Декодируем base64 строку
    # decoded = base64.b64decode(b).decode('utf-8')

    # Преобразуем JSON строку в словарь
    # result = json.loads(decoded)
    # print(result)
    return {
        'statusCode': 200,
        'body': 'Hello World!',
    }
## Лицензия

MIT 