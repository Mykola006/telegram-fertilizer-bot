import os
import requests
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

def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in ["N", "P", "K"])

# Функція створення графіків
async def generate_fertilizer_chart(data):
    elements = list(data.keys())
    values = list(data.values())
    plt.figure(figsize=(6, 4))
    plt.bar(elements, values, color=['blue', 'green', 'red'])
    plt.xlabel("Елементи")
    plt.ylabel("Кількість (кг/га)")
    plt.title("Рекомендовані добрива")
    plt.savefig("fertilizer_chart.png")
    return "fertilizer_chart.png"

# Функція нагадувань
async def send_fertilization_reminders(chat_id, schedule):
    for date, task in schedule.items():
        await bot.send_message(chat_id, f"📅 Нагадування: {task} на {date}")

@dp.message(lambda message: message.text in regions)
async def select_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
    weather_info = get_weather_data(message.text)
    await message.answer(f"Ви обрали {message.text} область. Останні метеодані: {weather_info}")

@dp.message(lambda message: message.text in moisture_zones)
async def calculate_fertilizers(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if not all(key in user_data for key in ["crop", "soil", "previous_crop", "region"]):
        await message.answer("⚠️ Виникла помилка! Почніть спочатку.")
        return
    
    crop, soil, prev_crop, moisture, region = user_data["crop"], user_data["soil"], user_data["previous_crop"], message.text, user_data["region"]
    weather_info = get_weather_data(region)
    fertilizer_rates = {"N": 120, "P": 60, "K": 90}  # Заглушка для тесту
    total_cost = calculate_fertilizer_cost(fertilizer_rates)
    chart_path = await generate_fertilizer_chart(fertilizer_rates)

    response = f"""
🔍 **Аналітичні дані**:
🌾 Культура: {crop}
🪵 Попередник: {prev_crop}
🌍 Тип ґрунту: {soil}
💧 Зона зволоження: {moisture}
📍 Область: {region}
☁️ Останні метеодані: {weather_info}
💰 Орієнтовна вартість добрив: {total_cost} $/га
"""
    await message.answer(response)
    await bot.send_photo(message.chat.id, photo=open(chart_path, 'rb'))

if __name__ == "__main__":
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
