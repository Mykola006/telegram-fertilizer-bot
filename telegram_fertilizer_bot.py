import os

try:
    import requests
except ModuleNotFoundError:
    import os
    os.system("pip install requests")
    import requests

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    import os
    os.system("pip install matplotlib")
    import matplotlib.pyplot as plt

import numpy as np
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
from aiohttp import web

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Помилка: TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/{TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Ініціалізація бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = web.Application()

# Список культур, типів ґрунту, попередників, областей
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий"]
previous_crops = ["Зернові", "Бобові", "Олійні"]
moisture_zones = ["Низька", "Середня", "Достатня"]
regions = ["Київська", "Львівська", "Вінницька", "Одеська", "Харківська", "Полтавська", "Черкаська"]

# Додаткові параметри
price_per_kg = {"N": 0.8, "P": 1.2, "K": 1.0}  # Ціни на добрива
base_yield = 6.0  # Базова врожайність у т/га

def get_weather_data(region):
    weather_api_url = f"https://api.open-meteo.com/v1/forecast?latitude=49.0&longitude=32.0&daily=precipitation_sum&timezone=Europe/Kiev"
    response = requests.get(weather_api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get("daily", {}).get("precipitation_sum", "Немає даних")
    return "Немає даних"

def calculate_fertilizer_needs(crop, soil, prev_crop, moisture):
    fertilizer_recommendations = {
        "Пшениця": {"N": 120, "P": 60, "K": 90},
        "Кукурудза": {"N": 150, "P": 80, "K": 100},
        "Соняшник": {"N": 90, "P": 50, "K": 70},
    }
    
    soil_adjustments = {
        "Чорнозем": {"N": 1.0, "P": 1.0, "K": 1.0},
        "Супіщаний": {"N": 1.2, "P": 1.1, "K": 1.2},
        "Глинистий": {"N": 0.9, "P": 1.0, "K": 0.9},
    }
    
    prev_crop_adjustments = {
        "Зернові": {"N": 1.1, "P": 1.0, "K": 1.0},
        "Бобові": {"N": 0.8, "P": 1.1, "K": 1.1},
        "Олійні": {"N": 1.0, "P": 1.0, "K": 1.0},
    }
    
    moisture_adjustments = {
        "Низька": {"N": 0.9, "P": 1.0, "K": 1.0},
        "Середня": {"N": 1.0, "P": 1.0, "K": 1.0},
        "Достатня": {"N": 1.1, "P": 1.1, "K": 1.1},
    }
    
    base = fertilizer_recommendations.get(crop, {"N": 0, "P": 0, "K": 0})
    adjusted = {
        "N": round(base["N"] * soil_adjustments[soil]["N"] * prev_crop_adjustments[prev_crop]["N"] * moisture_adjustments[moisture]["N"]),
        "P": round(base["P"] * soil_adjustments[soil]["P"] * prev_crop_adjustments[prev_crop]["P"] * moisture_adjustments[moisture]["P"]),
        "K": round(base["K"] * soil_adjustments[soil]["K"] * prev_crop_adjustments[prev_crop]["K"] * moisture_adjustments[moisture]["K"]),
    }
    return adjusted

if __name__ == "__main__":
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
