import os
import logging
import requests
import numpy as np
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiohttp import web

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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

# База даних по добривах
fertilizer_db = {
    "Пшениця": {"N": 120, "P": 60, "K": 90, "S": 10, "Zn": 0.5, "pH": 6.2},
    "Кукурудза": {"N": 150, "P": 80, "K": 100, "S": 15, "Zn": 1.0, "pH": 6.5},
    "Соняшник": {"N": 90, "P": 50, "K": 70, "S": 20, "B": 0.8, "pH": 6.3},
    "Ріпак": {"N": 180, "P": 90, "K": 110, "S": 25, "B": 1.0, "pH": 6.5},
    "Ячмінь": {"N": 110, "P": 55, "K": 80, "S": 12, "Cu": 0.3, "pH": 6.1},
    "Соя": {"N": 50, "P": 40, "K": 60, "S": 8, "pH": 6.8}
}

price_per_kg = {"N": 0.8, "P": 1.2, "K": 1.0, "S": 0.5, "Zn": 10, "B": 15, "Cu": 8}  # Ціни на добрива

# Функції аналітичної моделі
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
    plt.bar(elements, values, color=['blue', 'green', 'red', 'yellow', 'purple'])
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запускається...")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
