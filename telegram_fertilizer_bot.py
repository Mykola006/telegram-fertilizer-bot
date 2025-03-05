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
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
import asyncio

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Помилка: TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")

# Ініціалізація бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список культур, типів ґрунту, попередників, областей
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий"]
previous_crops = ["Зернові", "Бобові", "Олійні"]
moisture_zones = ["Низька", "Середня", "Достатня"]
regions = ["Київська", "Львівська", "Вінницька", "Одеська", "Харківська", "Полтавська", "Черкаська"]

# База даних культур та потреб у добривах
fertilizer_db = {
    "Пшениця": {"N": 120, "P": 60, "K": 90, "pH": 6.2},
    "Кукурудза": {"N": 150, "P": 80, "K": 100, "pH": 6.5},
    "Соняшник": {"N": 90, "P": 50, "K": 70, "pH": 6.3},
    "Ріпак": {"N": 180, "P": 90, "K": 110, "pH": 6.5},
    "Ячмінь": {"N": 110, "P": 55, "K": 80, "pH": 6.1},
    "Соя": {"N": 50, "P": 40, "K": 60, "pH": 6.8}
}

# Додаткові параметри
price_per_kg = {"N": 0.8, "P": 1.2, "K": 1.0}  # Ціни на добрива

# Баланс поживних речовин після попередньої культури
previous_crop_balance = {
    "Зернові": {"N": -20, "P": 0, "K": -10},
    "Бобові": {"N": 30, "P": 5, "K": 10},
    "Олійні": {"N": -10, "P": -5, "K": -15}
}

# Функція розрахунку потреби у добривах з урахуванням залишків
def calculate_adjusted_fertilizers(crop, prev_crop):
    base_needs = fertilizer_db[crop]
    adjustments = previous_crop_balance.get(prev_crop, {"N": 0, "P": 0, "K": 0})
    return {
        "N": max(0, base_needs["N"] + adjustments["N"]),
        "P": max(0, base_needs["P"] + adjustments["P"]),
        "K": max(0, base_needs["K"] + adjustments["K"]),
    }

# Кліматичні фактори (опади)
def get_climatic_adjustment(region):
    climatic_data = {
        "Київська": 600,
        "Львівська": 700,
        "Вінницька": 550,
        "Одеська": 400,
        "Харківська": 500,
        "Полтавська": 520,
        "Черкаська": 580
    }
    avg_rainfall = climatic_data.get(region, 550)
    if avg_rainfall < 500:
        return {"N": -10, "P": 0, "K": -5}
    elif avg_rainfall > 650:
        return {"N": 10, "P": 5, "K": 5}
    return {"N": 0, "P": 0, "K": 0}

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🌱 Обрати культуру"))
    keyboard.add(KeyboardButton("ℹ️ Інформація про бота"))
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=keyboard)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запускається...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
