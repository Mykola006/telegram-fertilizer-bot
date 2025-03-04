import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# Завантажуємо змінні середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Варіанти вибору
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Головне меню
main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🌱 Обрати культуру")],
    [KeyboardButton(text="ℹ️ Інформація про бота")]
], resize_keyboard=True)

# Функція створення клавіатури
def create_keyboard(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=option)] for option in options],
        resize_keyboard=True
    )

# Обробник команди /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення.\nОберіть культуру:", reply_markup=main_keyboard)

# Обробник кнопки "Інформація про бота"
@dp.message(F.text == "ℹ️ Інформація про бота")
async def send_info(message: Message):
    await message.answer("ℹ️ Детальніше про бота: [Сайт](https://sites.google.com/view/agronom-bot/)", parse_mode="Markdown")

# Обробник вибору культури
@dp.message(F.text == "🌱 Обрати культуру")
async def select_crop(message: Message, state: FSMContext):
    await message.answer("Будь ласка, оберіть культуру:", reply_markup=create_keyboard(crops))

@dp.message(F.text.in_(crops))
async def select_soil(message: Message, state: FSMContext):
    await state.update_data(crop=message.text)
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

@dp.message(F.text.in_(soil_types))
async def select_previous_crop(message: Message, state: FSMContext):
    await state.update_data(soil=message.text)
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть попередник:", reply_markup=create_keyboard(previous_crops))

@dp.message(F.text.in_(previous_crops))
async def select_moisture_zone(message: Message, state: FSMContext):
    await state.update_data(previous_crop=message.text)
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))

@dp.message(F.text.in_(moisture_zones))
async def calculate_fertilizer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    crop = user_data.get("crop")
    soil = user_data.get("soil")
    previous_crop = user_data.get("previous_crop")
    moisture = message.text

    # Розрахункові дані
    recommendations = {
        "Кукурудза": {"NPK": ("10-26-26", 200, 80), "Азот": ("КАС 32", 100, 50), "Сірка": ("Сульфат амонію", 50, 30), "Врожайність": "10 т/га"},
        "Пшениця": {"NPK": ("16-16-16", 150, 70), "Азот": ("Селітра аміачна", 90, 45), "Сірка": ("Гіпс", 30, 20), "Врожайність": "7 т/га"},
        "Соняшник": {"NPK": ("8-20-30", 180, 85), "Азот": ("Карбамід", 70, 40), "Сірка": ("Сульфат калію", 40, 25), "Врожайність": "4 т/га"}
    }

    recommendation = recommendations.get(crop, {})
    
    response = f"🌿 <b>Рекомендації для {crop}</b>\n"
    response += f"🟢 Попередник: {previous_crop}\n"
    response += f"🌱 Ґрунт: {soil}\n"
    response += f"💧 Зона зволоження: {moisture}\n"
    response += f"🌾 Планова врожайність: {recommendation.get('Врожайність', 'Не визначено')}\n\n"
    
    response += f"⚗️ <b>Комплексні добрива:</b>\n"
    response += f"🔹 {recommendation['NPK'][0]} - {recommendation['NPK'][1]} кг/га (~{recommendation['NPK'][2]}$/га)\n\n"
    
    response += f"⚗️ <b>Азотні добрива:</b>\n"
    response += f"🔹 {recommendation['Азот'][0]} - {recommendation['Азот'][1]} кг/га (~{recommendation['Азот'][2]}$/га)\n\n"
    
    response += f"⚗️ <b>Сірчані добрива:</b>\n"
    response += f"🔹 {recommendation['Сірка'][0]} - {recommendation['Сірка'][1]} кг/га (~{recommendation['Сірка'][2]}$/га)\n\n"

    buttons = [
        [InlineKeyboardButton(text="🔄 Обрати іншу культуру", callback_data="restart")],
        [InlineKeyboardButton(text="🌿 Змінити марки добрив", callback_data="change_fertilizer")],
        [InlineKeyboardButton(text="💳 Придбати розширений аналіз ($10)", callback_data="buy_premium")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(response, reply_markup=keyboard)

@dp.callback_query(F.data == "restart")
async def restart_process(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer("🔄 Почнемо спочатку! Оберіть культуру:", reply_markup=create_keyboard(crops))

@dp.callback_query(F.data == "buy_premium")
async def buy_premium(callback_query: types.CallbackQuery):
    await callback_query.message.answer("💳 Оплата тимчасово недоступна. Для консультацій пишіть: simoxa@ukr.net")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
