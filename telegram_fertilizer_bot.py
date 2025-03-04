import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMINS = os.getenv("ADMIN_IDS", "").split(',')  # ID адміністраторів через кому

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Дані для клавіатури
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Функція створення клавіатури
def create_keyboard(options):
def create_keyboard(options):
    keyboard = [[KeyboardButton(text=option)] for option in options]  # Виправлений формат
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Перевірка доступу адміністратора
def is_admin(user_id):
    return str(user_id) in ADMINS

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
        
        recommendation = {
            "NPK": "10-26-26",
            "Sulfur": "5-10 кг",
            "Nitrogen": "50-100 кг",
            "Cost_per_ha": "120$"
        }
        response = (
            f"Рекомендована марка добрив: {recommendation['NPK']}\n"
            f"Сірка: {recommendation['Sulfur']}\n"
            f"Азот: {recommendation['Nitrogen']}\n"
            f"Середня вартість на 1 га: {recommendation['Cost_per_ha']}"
        )
        await message.answer(response)

# Функція запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
