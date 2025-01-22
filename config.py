import os
from dotenv import load_dotenv
import json

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
with open('tokens.json') as f:
    tokens = json.load(f)
    TOKEN = tokens['telegram']

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
