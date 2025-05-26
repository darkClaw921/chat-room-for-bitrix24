import base64
import requests
import json

# # Открываем файл в бинарном режиме
# with open('20250513-kimai-export.pdf', 'rb') as file:
#     # Читаем файл в бинарном режиме
#     pdf_data = file.read()

# # Кодируем данные в base64
# pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')


# response = requests.post(
#     url="http://localhost:8000/api/webhook/client-message",
#     headers={"Content-Type": "application/json"},
#     json={
#         "telegram_id": 400923372,
#         "text": "Отправляю вам документ",
#         "token": "your-secret-api-token-here",
#         "username": "client123",
#         "file": {
#             "name": "20250513-kimai-export.pdf",
#             "data": pdf_base64
#         }
#     })


