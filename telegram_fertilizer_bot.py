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

def adjust_for_soil_ph(soil_ph, target_ph=6.5):
    if soil_ph < target_ph:
        return f"Рекомендується внесення вапна: {round((target_ph - soil_ph) * 2, 1)} т/га"
    return "pH ґрунту в нормі, вапнування не потрібне."

def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in fertilizer_rates)

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
