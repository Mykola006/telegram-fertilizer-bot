import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Клавіатура головного меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("\U0001F331 Обрати культуру"))
main_keyboard.add(KeyboardButton("ℹ️ Інформація про бота"))

# Список культур, типів ґрунту, попередників
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий"]
previous_crops = ["Зернові", "Бобові", "Олійні"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Клавіатура для оплати
payment_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатити 10$", url="https://www.liqpay.ua/")]
    ]
)

# Обробник команди /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("\U0001F44B Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=main_keyboard)

# Вибір культури
@dp.message(lambda message: message.text == "\U0001F331 Обрати культуру")
async def select_crop(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for crop in crops:
        keyboard.add(KeyboardButton(crop))
    await message.answer("Будь ласка, оберіть культуру:", reply_markup=keyboard)

# Вибір типу ґрунту
@dp.message(lambda message: message.text in crops)
async def select_soil(message: types.Message, state: FSMContext):
    await state.update_data(crop=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for soil in soil_types:
        keyboard.add(KeyboardButton(soil))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть тип ґрунту:", reply_markup=keyboard)

# Вибір попередника
@dp.message(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message, state: FSMContext):
    await state.update_data(soil=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for prev_crop in previous_crops:
        keyboard.add(KeyboardButton(prev_crop))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть попередник:", reply_markup=keyboard)

# Вибір зони зволоження
@dp.message(lambda message: message.text in previous_crops)
async def select_moisture_zone(message: types.Message, state: FSMContext):
    await state.update_data(previous_crop=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for zone in moisture_zones:
        keyboard.add(KeyboardButton(zone))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер виберіть зону зволоження:", reply_markup=keyboard)

# Розрахунок добрив
@dp.message(lambda message: message.text in moisture_zones)
async def calculate_fertilizers(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    crop, soil, prev_crop, moisture = user_data.values()
    
    # Аналітична модель (спрощено)
    recommended_fertilizers = {
        "Комплексне": {"Марка": "NPK 10-26-26", "Норма": "200 кг/га", "Ціна": "$50/га"},
        "Азотне": {"Марка": "КАС-32", "Норма": "100 кг/га", "Ціна": "$30/га"},
        "Сірчане": {"Марка": "Сульфат амонію", "Норма": "50 кг/га", "Ціна": "$15/га"},
    }

    response = (f"\U0001F50D Аналітичні дані:\n"
                f"🌾 Культура: {crop}\n"
                f"🪵 Попередник: {prev_crop}\n"
                f"🌍 Тип ґрунту: {soil}\n"
                f"💧 Зона зволоження: {moisture}\n\n"
                f"📊 Рекомендовані добрива:\n"
                f"✔ {recommended_fertilizers['Комплексне']['Марка']} — {recommended_fertilizers['Комплексне']['Норма']} — {recommended_fertilizers['Комплексне']['Ціна']}\n"
                f"✔ {recommended_fertilizers['Азотне']['Марка']} — {recommended_fertilizers['Азотне']['Норма']} — {recommended_fertilizers['Азотне']['Ціна']}\n"
                f"✔ {recommended_fertilizers['Сірчане']['Марка']} — {recommended_fertilizers['Сірчане']['Норма']} — {recommended_fertilizers['Сірчане']['Ціна']}")
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Змінити марки добрив"))
    keyboard.add(KeyboardButton("\U0001F331 Обрати іншу культуру"))
    await message.answer(response, reply_markup=keyboard)

# Обробка вибору інших марок
@dp.message(lambda message: message.text == "🔄 Змінити марки добрив")
async def change_fertilizers(message: types.Message):
    await message.answer("\U0001F50D Виберіть інші марки добрив:", reply_markup=payment_keyboard)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
