
import logging
import pdfkit
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv
import os

# Завантаження токену
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Логування
logging.basicConfig(level=logging.INFO)

# Клавіатури для вибору параметрів
crop_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
crops = ["Пшениця", "Кукурудза", "Соя", "Соняшник", "Ріпак", "Ячмінь"]
crop_keyboard.add(*crops)

soil_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
soils = ["Чорнозем", "Сірий лісовий", "Піщаний", "Супіщаний"]
soil_keyboard.add(*soils)

previous_crop_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
previous_crops = ["Зернові", "Бобові", "Капустяні", "Кукурудза"]
previous_crop_keyboard.add(*previous_crops)

moisture_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
moisture_levels = ["Низька", "Середня", "Достатня"]
moisture_keyboard.add(*moisture_levels)

# Словник норм внесення добрив (прикладні значення)
fertilizer_recommendations = {
    "Пшениця": {"NPK": "10-26-26", "N": 100, "P": 50, "K": 40, "Ціна": 50},
    "Кукурудза": {"NPK": "12-24-12", "N": 120, "P": 60, "K": 30, "Ціна": 55},
    "Соя": {"NPK": "5-20-30", "N": 20, "P": 80, "K": 60, "Ціна": 45},
    "Соняшник": {"NPK": "8-22-22", "N": 60, "P": 50, "K": 50, "Ціна": 48},
}

user_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привіт! Я бот для розрахунку добрив. Оберіть культуру:", reply_markup=crop_keyboard)

@dp.message_handler(lambda message: message.text in crops)
async def select_crop(message: types.Message):
    user_data[message.from_user.id] = {"crop": message.text}
    await message.answer("Оберіть тип ґрунту:", reply_markup=soil_keyboard)

@dp.message_handler(lambda message: message.text in soils)
async def select_soil(message: types.Message):
    user_data[message.from_user.id]["soil"] = message.text
    await message.answer("Оберіть попередник:", reply_markup=previous_crop_keyboard)

@dp.message_handler(lambda message: message.text in previous_crops)
async def select_previous_crop(message: types.Message):
    user_data[message.from_user.id]["previous_crop"] = message.text
    await message.answer("Оберіть зону зволоження:", reply_markup=moisture_keyboard)

@dp.message_handler(lambda message: message.text in moisture_levels)
async def select_moisture(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["moisture"] = message.text
    crop = user_data[user_id]["crop"]
    
    recommendation = fertilizer_recommendations.get(crop, {})
    if recommendation:
        text = (
f"Рекомендована марка добрив: {recommendation['NPK']}"
"
            f"Норма азоту (N): {recommendation['N']} кг/га
"
            f"Норма фосфору (P): {recommendation['P']} кг/га
"
            f"Норма калію (K): {recommendation['K']} кг/га
"
            f"Середня вартість: {recommendation['Ціна']} $/га

"
            "Бажаєте отримати рекомендації у форматі PDF? Напишіть 'PDF'."
        )
        await message.answer(text)
    else:
        await message.answer("Немає даних для обраної культури.")

@dp.message_handler(lambda message: message.text.lower() == "pdf")
async def generate_pdf(message: types.Message):
    user_id = message.from_user.id
    crop = user_data[user_id]["crop"]
    recommendation = fertilizer_recommendations.get(crop, {})
    
    pdf_content = (
        f"Рекомендації по внесенню добрив для {crop}
"
        f"Тип ґрунту: {user_data[user_id]['soil']}
"
        f"Попередник: {user_data[user_id]['previous_crop']}
"
        f"Зона зволоження: {user_data[user_id]['moisture']}

"
f"Рекомендована марка добрив: {recommendation['NPK']}"
"
        f"Норма азоту (N): {recommendation['N']} кг/га
"
        f"Норма фосфору (P): {recommendation['P']} кг/га
"
        f"Норма калію (K): {recommendation['K']} кг/га
"
        f"Середня вартість: {recommendation['Ціна']} $/га
"
    )

    pdf_path = f"recommendation_{user_id}.pdf"
    pdfkit.from_string(pdf_content, pdf_path)

    with open(pdf_path, "rb") as pdf_file:
        await bot.send_document(message.chat.id, types.InputFile(pdf_file, filename="Recommendation.pdf"))

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
