import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

# Варіанти культур
crops = ["Кукурудза", "Пшениця", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Підзолистий", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]

# Головне меню
main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🌱 Обрати культуру")],
    [KeyboardButton(text="ℹ️ Інформація про бота")]
], resize_keyboard=True)

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=main_keyboard)

@dp.message(F.text == "🌱 Обрати культуру")
async def choose_crop(message: Message):
    keyboard = ReplyKeyboardBuilder()
    for crop in crops:
        keyboard.add(KeyboardButton(text=crop))
    keyboard.adjust(2)
    await message.answer("Будь ласка, оберіть культуру:", reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(crops))
async def choose_soil(message: Message, state: FSMContext):
    await state.update_data(crop=message.text)
    keyboard = ReplyKeyboardBuilder()
    for soil in soil_types:
        keyboard.add(KeyboardButton(text=soil))
    keyboard.adjust(2)
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть тип ґрунту:", reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(soil_types))
async def choose_previous_crop(message: Message, state: FSMContext):
    await state.update_data(soil=message.text)
    keyboard = ReplyKeyboardBuilder()
    for prev in previous_crops:
        keyboard.add(KeyboardButton(text=prev))
    keyboard.adjust(2)
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть попередник:", reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(previous_crops))
async def calculate_fertilizer(message: Message, state: FSMContext):
    data = await state.get_data()
    crop = data["crop"]
    soil = data["soil"]
    previous_crop = message.text
    
    # Визначення норми добрив
    fertilizers = {
        "Комплексні": "NPK 10-26-26",
        "Азотні": "Карбамід 46%",
        "Сірчані": "Сульфат амонію 21%"
    }
    
    recommendation = f"\n✅ <b>Рекомендації для {crop}</b>\n\n"
    recommendation += f"🌱 Попередник: {previous_crop}\n🧪 Ґрунт: {soil}\n\n"
    recommendation += f"🔹 Комплексне добриво: {fertilizers['Комплексні']} (200 кг/га)\n"
    recommendation += f"🔹 Азотне добриво: {fertilizers['Азотні']} (150 кг/га)\n"
    recommendation += f"🔹 Сірчане добриво: {fertilizers['Сірчані']} (100 кг/га)\n\n"
    recommendation += "💰 Орієнтовна вартість: 120$/га"
    
    # Додаткові кнопки
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌾 Обрати іншу культуру"), KeyboardButton(text="🔄 Альтернативні варіанти")],
        [KeyboardButton(text="💰 Придбати розширений розрахунок")]
    ], resize_keyboard=True)
    
    await message.answer(recommendation, reply_markup=keyboard)

@dp.message(F.text == "💰 Придбати розширений розрахунок")
async def buy_premium(message: Message):
    await message.answer("💳 Оплата поки що умовна. Після реєстрації в LiqPay додамо справжню оплату.")

@dp.message(F.text == "ℹ️ Інформація про бота")
async def bot_info(message: Message):
    await message.answer("ℹ️ Інформація про бота: https://sites.google.com/view/agronom-bot/")

@dp.message(F.text == "🌾 Обрати іншу культуру")
async def restart(message: Message):
    await choose_crop(message)

if __name__ == "__main__":
    import asyncio
    from aiogram import executor
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
