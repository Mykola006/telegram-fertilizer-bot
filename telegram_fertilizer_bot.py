import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ⚡ Головне меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌱 Обрати культуру")],
        [KeyboardButton(text="ℹ️ Інформація про бота")]
    ],
    resize_keyboard=True
)

# 🔹 Варіанти культур
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Підзолистий", "Глинистий", "Супіщаний"]
previous_crops_groups = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]

# 📌 Обробка команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=main_keyboard)

# 🌱 Обробник вибору культури
@dp.message(lambda message: message.text == "🌱 Обрати культуру")
async def select_crop(message: types.Message):
    crop_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=crop)] for crop in crops],
        resize_keyboard=True
    )
    await message.answer("Будь ласка, оберіть культуру:", reply_markup=crop_keyboard)

# 🏔 Обробка вибору ґрунту
@dp.message(lambda message: message.text in crops)
async def select_soil(message: types.Message):
    selected_crop = message.text
    soil_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=soil)] for soil in soil_types],
        resize_keyboard=True
    )
    await message.answer(f"✅ Ви обрали {selected_crop}. Тепер оберіть тип ґрунту:", reply_markup=soil_keyboard)

# 🌾 Обробка вибору попередника (група культур)
@dp.message(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message):
    selected_soil = message.text
    prev_crop_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=prev)] for prev in previous_crops_groups],
        resize_keyboard=True
    )
    await message.answer(f"✅ Ви обрали {selected_soil}. Тепер оберіть попередник (групу культур):", reply_markup=prev_crop_keyboard)

# 📊 Генерація рекомендацій
fertilizer_data = {
    "Зернові": {"complex_fertilizer": "NPK 10-26-26", "complex_rate": 150, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 100, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 50, "cost": 120},
    "Бобові": {"complex_fertilizer": "NPK 15-15-15", "complex_rate": 180, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 80, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 60, "cost": 110},
    "Технічні": {"complex_fertilizer": "NPK 12-24-12", "complex_rate": 160, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 110, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 55, "cost": 130},
    "Овочі": {"complex_fertilizer": "NPK 8-20-30", "complex_rate": 200, "nitrogen_fertilizer": "Селітра", "nitrogen_rate": 90, "sulfur_fertilizer": "Сульфат калію", "sulfur_rate": 70, "cost": 140},
    "Чистий пар": {"complex_fertilizer": "NPK 10-20-20", "complex_rate": 140, "nitrogen_fertilizer": "Селітра", "nitrogen_rate": 70, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 45, "cost": 100},
}

# 📝 Обробка вибору попередника та розрахунок добрив
@dp.message(lambda message: message.text in previous_crops_groups)
async def calculate_fertilizer(message: types.Message):
    selected_previous_crop = message.text
    recommendation = fertilizer_data.get(selected_previous_crop, fertilizer_data["Зернові"])
    await message.answer(
        f"💡 Рекомендація для попередника {selected_previous_crop}:
        \n📌 Комплексне добриво: {recommendation['complex_fertilizer']}, {recommendation['complex_rate']} кг/га
        \n📌 Азотні добрива: {recommendation['nitrogen_fertilizer']}, {recommendation['nitrogen_rate']} кг/га
        \n📌 Сірчані добрива: {recommendation['sulfur_fertilizer']}, {recommendation['sulfur_rate']} кг/га
        \n💰 Орієнтовна вартість: {recommendation['cost']}$/га",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔄 Обрати іншу культуру")],
                [KeyboardButton(text="⚙️ Альтернативні варіанти живлення")],
            ],
            resize_keyboard=True
        )
    )

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
