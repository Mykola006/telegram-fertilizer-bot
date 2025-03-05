import os
import asyncio
import logging
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Помилка: TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Оновлена база даних регіонів, ґрунтів та культур
regions = [
    "Волинська", "Дніпропетровська", "Донецька", "Житомирська", "Закарпатська", "Запорізька", "Івано-Франківська",
    "Київська", "Кіровоградська", "Луганська", "Львівська", "Миколаївська", "Одеська", "Полтавська", "Рівненська",
    "Сумська", "Тернопільська", "Харківська", "Херсонська", "Хмельницька", "Черкаська", "Чернівецька", "Чернігівська"
]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий", "Торфовий"]
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя", "Горох", "Цукровий буряк", "Картопля"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Оновлена база даних потреб у добривах з урахуванням запланованої врожайності
fertilizer_db = {
    "Пшениця": {"N": 30, "P": 12, "K": 18, "pH": 6.2},
    "Кукурудза": {"N": 35, "P": 14, "K": 20, "pH": 6.5},
    "Соняшник": {"N": 25, "P": 10, "K": 15, "pH": 6.3},
    "Ріпак": {"N": 40, "P": 16, "K": 22, "pH": 6.5},
    "Ячмінь": {"N": 28, "P": 11, "K": 17, "pH": 6.1},
    "Соя": {"N": 20, "P": 9, "K": 14, "pH": 6.8},
    "Горох": {"N": 15, "P": 7, "K": 10, "pH": 6.7},
    "Цукровий буряк": {"N": 50, "P": 20, "K": 30, "pH": 6.3},
    "Картопля": {"N": 45, "P": 18, "K": 25, "pH": 5.8}
}

# Функція створення клавіатури

def create_keyboard(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=option)] for option in options],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📊 Розрахунок добрив")]],
        resize_keyboard=True
    )
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Натисніть кнопку нижче, щоб розпочати тестування.", reply_markup=keyboard)

@dp.message(F.text == "📊 Розрахунок добрив")
async def fertilizer_calculation(message: types.Message):
    keyboard = create_keyboard(crops)
    await message.answer("Оберіть культуру:", reply_markup=keyboard)

@dp.message(F.text.in_(crops))
async def get_crop_choice(message: types.Message):
    crop = message.text
    await message.answer("Введіть заплановану врожайність (т/га):", reply_markup=ReplyKeyboardRemove())
    dp.fsm_context.set_data({"crop": crop})

@dp.message(F.text.isdigit())
async def get_yield_goal(message: types.Message):
    yield_goal = int(message.text)
    await message.answer("Оберіть площу поля (га):")
    dp.fsm_context.update_data({"yield_goal": yield_goal})

@dp.message(F.text.isdigit())
async def get_field_area(message: types.Message):
    area = int(message.text)
    data = await dp.fsm_context.get_data()
    crop = data.get("crop", "Кукурудза")
    yield_goal = data.get("yield_goal", 5)
    fertilizers = calculate_fertilizer_rates(crop, yield_goal)
    total_cost = calculate_total_cost(fertilizers, area)
    result = f"📊 Розрахунок:
    🔹 Культура: {crop}
    🔹 Запланована врожайність: {yield_goal} т/га
    🔹 Загальна площа: {area} га
    🔹 Добрива:
    - Азот (N): {fertilizers['N']} кг/га
    - Фосфор (P): {fertilizers['P']} кг/га
    - Калій (K): {fertilizers['K']} кг/га
    💰 Загальна вартість: {total_cost:.2f} USD"
    await message.answer(result, reply_markup=ReplyKeyboardRemove())

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запускається...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
