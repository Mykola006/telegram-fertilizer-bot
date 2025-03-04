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
previous_crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]

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

# 🌾 Обробка вибору попередника
@dp.message(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message):
    selected_soil = message.text
    prev_crop_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=prev)] for prev in previous_crops],
        resize_keyboard=True
    )
    await message.answer(f"✅ Ви обрали {selected_soil}. Тепер оберіть попередник:", reply_markup=prev_crop_keyboard)

# 📊 Генерація рекомендацій
def generate_fertilizer_recommendation(previous_crop):
    fertilizer_data = {
        "Пшениця": {"complex_fertilizer": "NPK 10-26-26", "complex_rate": 150, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 100, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 50, "cost": 120},
        "Кукурудза": {"complex_fertilizer": "NPK 15-15-15", "complex_rate": 200, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 120, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 40, "cost": 150},
        "Соняшник": {"complex_fertilizer": "NPK 12-24-12", "complex_rate": 180, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 90, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 60, "cost": 130},
    }
    return fertilizer_data.get(previous_crop, fertilizer_data["Пшениця"])

# 📝 Обробка вибору попередника та розрахунок добрив
@dp.message(lambda message: message.text in previous_crops)
async def calculate_fertilizer(message: types.Message):
    selected_previous_crop = message.text
    recommendation = generate_fertilizer_recommendation(selected_previous_crop)

    await message.answer(
        f"💡 Рекомендація для {selected_previous_crop}:\n\n"
        f"📌 Комплексне добриво: {recommendation['complex_fertilizer']}, {recommendation['complex_rate']} кг/га\n"
        f"📌 Азотні добрива: {recommendation['nitrogen_fertilizer']}, {recommendation['nitrogen_rate']} кг/га\n"
        f"📌 Сірчані добрива: {recommendation['sulfur_fertilizer']}, {recommendation['sulfur_rate']} кг/га\n"
        f"💰 Орієнтовна вартість: {recommendation['cost']}$/га",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔄 Обрати іншу культуру")],
                [KeyboardButton(text="⚙️ Альтернативні варіанти живлення")],
            ],
            resize_keyboard=True
        )
    )

# 💳 Оплата
@dp.message(lambda message: message.text == "💳 Отримати детальний розрахунок (10$)")
async def process_payment(message: types.Message):
    await message.answer(
        "💳 Для отримання детального розрахунку натисніть кнопку нижче:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Оплатити через LiqPay", url="https://www.liqpay.ua/")]
            ]
        )
    )

# ℹ️ Інформація про бота
@dp.message(lambda message: message.text == "ℹ️ Інформація про бота")
async def bot_info(message: types.Message):
    await message.answer(
        "ℹ️ Дізнайтесь більше про нашого бота тут: [Агроном у смартфоні](https://sites.google.com/view/agronom-bot/)",
        parse_mode="Markdown"
    )

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
