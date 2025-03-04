
# Завантажте ваш оригінальний код у цей файл

import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Створюємо клавіатуру для вибору культури
culture_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
cultures = ["Пшениця", "Кукурудза", "Соя", "Соняшник", "Ячмінь", "Ріпак"]
for culture in cultures:
    culture_keyboard.add(KeyboardButton(culture))

# Створюємо клавіатуру для вибору типу ґрунту
soil_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
soils = ["Чорнозем", "Підзолистий", "Глинистий", "Супіщаний"]
for soil in soils:
    soil_keyboard.add(KeyboardButton(soil))

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Виберіть культуру:", reply_markup=culture_keyboard)

@dp.message_handler(lambda message: message.text in cultures)
async def select_culture(message: types.Message):
    await message.answer("Виберіть тип ґрунту:", reply_markup=soil_keyboard)

@dp.message_handler(lambda message: message.text in soils)
async def select_soil(message: types.Message):
    await message.answer("Введіть площу поля у гектарах:")

@dp.message_handler(lambda message: message.text.isdigit())
async def calculate_fertilizer(message: types.Message):
    hectares = int(message.text)
    recommended_fertilizer = f"Рекомендована марка добрив: NPK 10-26-26
Норма внесення: {hectares * 120} кг/га"
    await message.answer(recommended_fertilizer)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
