import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Налаштування бота
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

# Варіанти культур, типів ґрунту, попередників
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Підзолистий", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for option in options:
        keyboard.add(KeyboardButton(option))
    return keyboard

# Головне меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🌱 Обрати культуру"), KeyboardButton("ℹ️ Інформація про бота"))

# Обробник команди /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:",
                        reply_markup=create_keyboard(crops))

# Вибір культури
@dp.message_handler(lambda message: message.text in crops)
async def select_soil(message: types.Message):
    crop = message.text
    await message.reply(f"✅ Ви обрали: {crop}. Тепер оберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

# Вибір ґрунту
@dp.message_handler(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message):
    soil = message.text
    await message.reply(f"✅ Ви обрали: {soil}. Тепер оберіть попередник:", reply_markup=create_keyboard(previous_crops))

# Вибір попередника
@dp.message_handler(lambda message: message.text in previous_crops)
async def select_moisture_zone(message: types.Message):
    prev_crop = message.text
    await message.reply(f"✅ Ви обрали: {prev_crop}. Тепер виберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))

# Вибір зони зволоження
@dp.message_handler(lambda message: message.text in moisture_zones)
async def calculate_fertilizer(message: types.Message):
    moisture = message.text
    await message.reply(f"✅ Ви обрали зону зволоження: {moisture}. Розраховуємо норму добрив...")

    # Логіка розрахунку добрив
    recommendation = {
        "NPK": "10-26-26",  # Комплексне добриво
        "Sulfur": "5-10 кг",
        "Nitrogen": "50-100 кг",
        "Cost_per_ha": "120$"
    }

    response = (
        f"✅ <b>Рекомендована марка добрив:</b> {recommendation['NPK']}\n"
        f"🌿 <b>Сірка:</b> {recommendation['Sulfur']}\n"
        f"⚡ <b>Азот:</b> {recommendation['Nitrogen']}\n"
        f"💰 <b>Середня вартість на 1 га:</b> {recommendation['Cost_per_ha']}"
    )

    await message.reply(response, reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("🔄 Змінити марки добрив"), KeyboardButton("✅ Врахувати аналіз ґрунту")
    ))

# Обробка кнопки "Врахувати аналіз ґрунту"
@dp.message_handler(lambda message: message.text == "✅ Врахувати аналіз ґрунту")
async def handle_analysis_request(message: types.Message):
    await message.reply("📊 Для детального аналізу звертайтесь: simoxa@ukr.net")

# Обробка кнопки "Змінити марки добрив"
@dp.message_handler(lambda message: message.text == "🔄 Змінити марки добрив")
async def change_fertilizer_brands(message: types.Message):
    await message.reply("💡 Оберіть інші марки добрив:", reply_markup=create_keyboard(["NPK 12-24-12", "NPK 15-15-15", "NPK 20-20-20"]))

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
