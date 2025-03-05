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
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
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

# Функція розрахунку вартості добрив
def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in fertilizer_rates)

# Функція для розширеного аналізу умов вирощування
def advanced_fertilizer_analysis(crop, soil, prev_crop, region):
    base_fertilizers = fertilizer_db[crop]
    # Врахування кліматичних умов
    climatic_factors = {"Київська": 1.0, "Львівська": 1.1, "Одеська": 0.9, "Полтавська": 1.05}
    climate_adjustment = climatic_factors.get(region, 1.0)
    
    # Врахування залишків поживних речовин
    prev_crop_impact = {"Зернові": {"N": -10, "P": 0, "K": -5}, "Бобові": {"N": 20, "P": 5, "K": 10}}
    crop_impact = prev_crop_impact.get(prev_crop, {"N": 0, "P": 0, "K": 0})
    
    adjusted_fertilizers = {
        "N": max(0, base_fertilizers["N"] + crop_impact["N"] * climate_adjustment),
        "P": max(0, base_fertilizers["P"] + crop_impact["P"] * climate_adjustment),
        "K": max(0, base_fertilizers["K"] + crop_impact["K"] * climate_adjustment),
    }
    
    return adjusted_fertilizers, calculate_fertilizer_cost(adjusted_fertilizers)

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton("🌱 Обрати культуру")],
        [KeyboardButton("📊 Отримати аналіз"), KeyboardButton("💰 Порівняти витрати")],
        [KeyboardButton("📄 Отримати звіт")]
    ])
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть дію:", reply_markup=keyboard)

@dp.message(lambda message: message.text == "📄 Отримати звіт")
async def send_report(message: types.Message):
    crop = "Кукурудза"
    soil = "Чорнозем"
    prev_crop = "Зернові"
    region = "Київська"
    fertilizers, cost = advanced_fertilizer_analysis(crop, soil, prev_crop, region)
    data = f"""
    🚜 **Агроаналітичний звіт**
    📍 Культура: {crop}
    🌱 Тип ґрунту: {soil}
    🔄 Попередник: {prev_crop}
    📍 Регіон: {region}
    📊 Рекомендовані добрива:
    - Азот (N): {fertilizers['N']} кг/га
    - Фосфор (P): {fertilizers['P']} кг/га
    - Калій (K): {fertilizers['K']} кг/га
    💰 Загальна вартість: {cost} $/га
    """
    with open("fertilizer_report.txt", "w", encoding="utf-8") as file:
        file.write(data)
    await message.answer_document(InputFile("fertilizer_report.txt"))

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запускається...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
