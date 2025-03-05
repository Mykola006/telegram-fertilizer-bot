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

# Розширена база даних по культурах і добривах
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
base_yield = 6.0  # Базова врожайність у т/га

def adjust_for_soil_ph(soil_ph, target_ph=6.5):
    if soil_ph < target_ph:
        return f"Рекомендується внесення вапна: {round((target_ph - soil_ph) * 2, 1)} т/га"
    return "pH ґрунту в нормі, вапнування не потрібне."

def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in fertilizer_rates)

def generate_fertilizer_chart(fertilizer_rates):
    elements = list(fertilizer_rates.keys())
    values = list(fertilizer_rates.values())
    plt.figure(figsize=(6, 4))
    plt.bar(elements, values, color=['blue', 'green', 'red'])
    plt.xlabel("Елементи")
    plt.ylabel("Кількість (кг/га)")
    plt.title("Рекомендовані добрива")
    plt.savefig("fertilizer_chart.png")
    return "fertilizer_chart.png"

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🌱 Обрати культуру"))
    keyboard.add(KeyboardButton("ℹ️ Інформація про бота"))
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=keyboard)

@dp.message(lambda message: message.text in crops)
async def select_soil(message: types.Message, state: FSMContext):
    await state.update_data(crop=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for soil in soil_types:
        keyboard.add(KeyboardButton(soil))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть тип ґрунту:", reply_markup=keyboard)

@dp.message(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message, state: FSMContext):
    await state.update_data(soil=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for prev_crop in previous_crops:
        keyboard.add(KeyboardButton(prev_crop))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть попередник:", reply_markup=keyboard)

@dp.message(lambda message: message.text in previous_crops)
async def calculate_fertilizers(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    crop = user_data.get("crop")
    soil = user_data.get("soil")
    prev_crop = message.text
    
    if crop not in fertilizer_db:
        await message.answer("⚠️ Помилка! Дані для цієї культури відсутні.")
        return
    
    fertilizer_recommendations = fertilizer_db[crop]
    ph_recommendation = adjust_for_soil_ph(fertilizer_recommendations["pH"])
    total_cost = calculate_fertilizer_cost(fertilizer_recommendations)
    
    response = f"""
🔍 **Аналітичні дані**:
🌾 Культура: {crop}
🌍 Тип ґрунту: {soil}
🪵 Попередник: {prev_crop}
📊 Рекомендовані добрива (кг/га): {fertilizer_recommendations}
💰 Орієнтовна вартість добрив: {total_cost} $/га
⚖️ {ph_recommendation}
"""
    await message.answer(response)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(start)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
