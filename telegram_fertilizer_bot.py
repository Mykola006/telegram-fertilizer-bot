import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Варіанти культур
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for option in options:
        keyboard.add(KeyboardButton(option))
    return keyboard

# Обробник команди /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Вітаю! Оберіть культуру:", reply_markup=create_keyboard(crops))

# Обробник вибору культури
@dp.message_handler(lambda message: message.text in crops)
async def select_soil(message: types.Message):
    crop = message.text
    await message.reply(f"Ви обрали: {crop}. Тепер виберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

# Обробник вибору ґрунту
@dp.message_handler(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message):
    soil = message.text
    await message.reply(f"Ви обрали: {soil}. Тепер виберіть попередник:", reply_markup=create_keyboard(previous_crops))

# Обробник вибору попередника
@dp.message_handler(lambda message: message.text in previous_crops)
async def select_moisture_zone(message: types.Message):
    prev_crop = message.text
    await message.reply(f"Ви обрали: {prev_crop}. Тепер виберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))

# Обробник вибору зони зволоження
@dp.message_handler(lambda message: message.text in moisture_zones)
async def calculate_fertilizer(message: types.Message):
    moisture = message.text
    await message.reply(f"Ви обрали зону зволоження: {moisture}. Тепер розрахуємо необхідну кількість добрив.")

    # Тут можна додати логіку розрахунку добрив
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


    await message.reply(response)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
