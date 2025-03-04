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

# Ініціалізація бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Варіанти вибору
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Дані про добрива (приклад)
fertilizer_data = {
    "Пшениця": {"NPK": "10-26-26", "Rate": "150-180 кг/га"},
    "Кукурудза": {"NPK": "16-16-16", "Rate": "200-250 кг/га"},
    "Соняшник": {"NPK": "8-24-24", "Rate": "100-140 кг/га"},
    "Ріпак": {"NPK": "12-24-12", "Rate": "180-220 кг/га"},
    "Ячмінь": {"NPK": "10-20-20", "Rate": "140-170 кг/га"},
    "Соя": {"NPK": "5-20-30", "Rate": "90-120 кг/га"},
}

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = [[KeyboardButton(text=option)] for option in options]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Збереження вибору користувача
user_selection = {}

# Обробник команди /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_selection[message.chat.id] = {}
    await message.answer("Вітаю! Оберіть культуру:", reply_markup=create_keyboard(crops))

# Обробники вибору
@dp.message()
async def handle_message(message: Message):
    user_id = message.chat.id
    text = message.text

    if text in crops:
        user_selection[user_id]["crop"] = text
        await message.answer(f"Ви обрали культуру: <b>{text}</b>. Тепер виберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

    elif text in soil_types:
        user_selection[user_id]["soil"] = text
        await message.answer(f"Ви обрали тип ґрунту: <b>{text}</b>. Тепер виберіть попередник:", reply_markup=create_keyboard(previous_crops))

    elif text in previous_crops:
        user_selection[user_id]["previous_crop"] = text
        await message.answer(f"Ви обрали попередник: <b>{text}</b>. Тепер виберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))

    elif text in moisture_zones:
        user_selection[user_id]["moisture"] = text
        await message.answer(f"Ви обрали зону зволоження: <b>{text}</b>. Розраховую добрива...")

        # Отримуємо дані про добриво
        crop = user_selection[user_id].get("crop", "Пшениця")
        fertilizer = fertilizer_data.get(crop, {"NPK": "10-26-26", "Rate": "150 кг/га"})

        # Логіка коригування норми внесення залежно від умов
        rate = fertilizer["Rate"]
        if text == "Низька":
            rate = str(int(rate.split("-")[0]) - 10) + "-" + str(int(rate.split("-")[1]) - 10) + " кг/га"
        elif text == "Достатня":
            rate = str(int(rate.split("-")[0]) + 10) + "-" + str(int(rate.split("-")[1]) + 10) + " кг/га"

        # Формування відповіді
        response = (
            f"✅ <b>Рекомендована марка добрив:</b> {fertilizer['NPK']}\n"
            f"💰 <b>Рекомендована норма:</b> {rate}\n"
            f"🌱 <b>Враховано:</b> культура {crop}, тип ґрунту {user_selection[user_id].get('soil', '-')}, "
            f"попередник {user_selection[user_id].get('previous_crop', '-')}, зона зволоження {text}."
        )
        await message.answer(response, parse_mode="HTML")

# Функція запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
