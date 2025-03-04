import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
from aiohttp import web

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/{TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Ініціалізація бота
bot = Bot(token=TOKEN)
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

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
    required_keys = ["crop", "soil", "previous_crop"]
    
    if not all(key in user_data for key in required_keys):
        await message.answer("⚠️ Виникла помилка! Будь ласка, почніть спочатку, обравши культуру.", reply_markup=main_keyboard)
        return
    
    crop, soil, prev_crop, moisture = user_data["crop"], user_data["soil"], user_data["previous_crop"], message.text
    
    response = (f"\U0001F50D Аналітичні дані:\n"
                f"🌾 Культура: {crop}\n"
                f"🪵 Попередник: {prev_crop}\n"
                f"🌍 Тип ґрунту: {soil}\n"
                f"💧 Зона зволоження: {moisture}")
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Змінити марки добрив"))
    keyboard.add(KeyboardButton("\U0001F331 Обрати іншу культуру"))
    await message.answer(response, reply_markup=keyboard)

# Запуск веб-сервера для webhook
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

async def on_shutdown():
    await bot.delete_webhook()

async def handle_update(request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return web.Response()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_update)

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
