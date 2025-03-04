import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Завантаження токена бота
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Варіанти вибору культур
cultures = ["Пшениця", "Кукурудза", "Ріпак", "Соняшник", "Соя", "Ячмінь"]
soil_types = ["Чорнозем", "Сірозем", "Підзолистий", "Супіщаний", "Глинистий"]
previous_crops = ["Пшениця", "Кукурудза", "Ріпак", "Соняшник", "Соя", "Ячмінь"]
moisture_zones = ["Низька", "Середня", "Достатня"]

fertilizer_recommendations = {
    "Пшениця": {"NPK": "10-26-26", "норма": 150, "ціна": 50},
    "Кукурудза": {"NPK": "12-24-12", "норма": 200, "ціна": 60},
    "Ріпак": {"NPK": "8-20-30", "норма": 180, "ціна": 55},
    "Соняшник": {"NPK": "10-20-20", "норма": 160, "ціна": 52},
    "Соя": {"NPK": "6-18-36", "норма": 140, "ціна": 48},
    "Ячмінь": {"NPK": "12-22-22", "норма": 170, "ціна": 58},
}

# Головна клавіатура
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for culture in cultures:
        keyboard.add(KeyboardButton(culture))
    return keyboard

def soil_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for soil in soil_types:
        keyboard.add(KeyboardButton(soil))
    return keyboard

def previous_crop_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for crop in previous_crops:
        keyboard.add(KeyboardButton(crop))
    return keyboard

def moisture_zone_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for zone in moisture_zones:
        keyboard.add(KeyboardButton(zone))
    return keyboard

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Оберіть культуру:", reply_markup=main_keyboard())

@dp.message_handler(lambda message: message.text in cultures)
async def select_culture(message: types.Message):
    user_data[message.from_user.id] = {"culture": message.text}
    await message.reply("Оберіть тип ґрунту:", reply_markup=soil_keyboard())

@dp.message_handler(lambda message: message.text in soil_types)
async def select_soil(message: types.Message):
    user_data[message.from_user.id]["soil"] = message.text
    await message.reply("Оберіть попередник:", reply_markup=previous_crop_keyboard())

@dp.message_handler(lambda message: message.text in previous_crops)
async def select_previous_crop(message: types.Message):
    user_data[message.from_user.id]["previous_crop"] = message.text
    await message.reply("Оберіть зону зволоження:", reply_markup=moisture_zone_keyboard())

@dp.message_handler(lambda message: message.text in moisture_zones)
async def select_moisture_zone(message: types.Message):
    user_data[message.from_user.id]["moisture_zone"] = message.text
    culture = user_data[message.from_user.id]["culture"]

    recommendation = fertilizer_recommendations.get(culture, {})
    if recommendation:
        response = (
            f"Рекомендована марка добрив: {recommendation['NPK']}
"
            f"Норма внесення: {recommendation['норма']} кг/га
"
            f"Орієнтовна вартість: {recommendation['ціна']} $/га"
        )
    else:
        response = "Немає даних для цієї культури."

    await message.reply(response)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
