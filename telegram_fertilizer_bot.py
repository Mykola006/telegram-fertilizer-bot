import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота з коректним `parse_mode`
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Варіанти вибору
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = [[KeyboardButton(text=option)] for option in options]  # Виправлено формат
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Обробник команди /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Вітаю! Оберіть культуру:", reply_markup=create_keyboard(crops))

# Обробники вибору
@dp.message()
async def handle_message(message: Message):
    text = message.text
    if text in crops:
        await message.answer(f"Ви обрали: {text}. Тепер виберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))
    elif text in soil_types:
        await message.answer(f"Ви обрали: {text}. Тепер виберіть попередник:", reply_markup=create_keyboard(previous_crops))
    elif text in previous_crops:
        await message.answer(f"Ви обрали: {text}. Тепер виберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))
    elif text in moisture_zones:
        await message.answer(f"Ви обрали зону зволоження: {text}. Розраховуємо добрива...")

        # Розрахунок добрив
        recommendation = {
            "NPK": "10-26-26",
            "Sulfur": "5-10 кг",
            "Nitrogen": "50-100 кг",
            "Cost_per_ha": "120$"
        }
        response = (
            f"✅ <b>Рекомендована марка добрив:</b> {recommendation['NPK']}\n"
            f"🌿 <b>Сірка:</b> {recommendation['Sulfur']}\n"
            f"🌱 <b>Азот:</b> {recommendation['Nitrogen']}\n"
            f"💰 <b>Середня вартість на 1 га:</b> {recommendation['Cost_per_ha']}"
        )
        await message.answer(response, parse_mode="HTML")

# Функція запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
