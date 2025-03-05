import os
import asyncio
import logging
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.filters import Command

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Помилка: TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

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
ph_adjustment = {"Чорнозем": 6.5, "Супіщаний": 5.5, "Глинистий": 6.0, "Підзолистий": 5.0}  # Рекомендоване pH

# Функція розрахунку вартості добрив
def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in fertilizer_rates)

# Функція для розширеного аналізу умов вирощування
def advanced_fertilizer_analysis(crop, soil, prev_crop, region):
    base_fertilizers = fertilizer_db[crop]
    climatic_factors = {"Київська": 1.0, "Львівська": 1.1, "Одеська": 0.9, "Полтавська": 1.05}
    climate_adjustment = climatic_factors.get(region, 1.0)
    prev_crop_impact = {"Зернові": {"N": -10, "P": 0, "K": -5}, "Бобові": {"N": 20, "P": 5, "K": 10}}
    crop_impact = prev_crop_impact.get(prev_crop, {"N": 0, "P": 0, "K": 0})
    
    adjusted_fertilizers = {
        "N": max(0, base_fertilizers["N"] + crop_impact["N"] * climate_adjustment),
        "P": max(0, base_fertilizers["P"] + crop_impact["P"] * climate_adjustment),
        "K": max(0, base_fertilizers["K"] + crop_impact["K"] * climate_adjustment),
    }
    
    # Коригування pH та вапнування
    soil_ph = ph_adjustment.get(soil, 6.0)
    ph_diff = soil_ph - base_fertilizers["pH"]
    if ph_diff < -0.5:
        adjusted_fertilizers["CaCO3"] = abs(ph_diff) * 100  # Додавання вапна
    
    return adjusted_fertilizers, calculate_fertilizer_cost(adjusted_fertilizers)

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌱 Обрати культуру")],
            [KeyboardButton(text="📊 Отримати аналіз"), KeyboardButton(text="💰 Порівняти витрати")],
            [KeyboardButton(text="📄 Отримати звіт")]
        ],
        resize_keyboard=True
    )
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть дію:", reply_markup=keyboard)

@dp.message(lambda message: message.text in ["🌱 Обрати культуру", "📊 Отримати аналіз", "💰 Порівняти витрати", "📄 Отримати звіт"])
async def handle_buttons(message: types.Message):
    await message.answer(f"Ви обрали: {message.text}")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запускається...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
