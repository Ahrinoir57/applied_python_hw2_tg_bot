import os
from dotenv import load_dotenv
import json

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TG_TOKEN = os.getenv("TG_TOKEN")
NINJA_TOKEN = os.getenv("NINJA_TOKEN")
CALORIE_TOKEN = os.getenv("CALORIE_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")

if not TG_TOKEN:
    raise ValueError("Переменная окружения TG_TOKEN не установлена!")
if not NINJA_TOKEN:
    raise ValueError("Переменная окружения NINJA_TOKEN не установлена!")
if not CALORIE_TOKEN:
    raise ValueError("Переменная окружения CALORIE_TOKEN не установлена!")
if not WEATHER_TOKEN:
    raise ValueError("Переменная окружения WEATHER_TOKEN не установлена!")
