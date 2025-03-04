import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_data import CallbackData
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Клавіатура для головного меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("🌱 Обрати культуру"))
main_keyboard.add(KeyboardButton("ℹ️ Інформація про бота"))

# Callback для вибору культури
crop_callback = CallbackData("crop", "name")

# Варіанти культур
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий"]
previous_crops = ["Зернові", "Бобові", "Технічні"]
moisture_zones = ["Низька", "Середня", "Достатня"]

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", 
                         reply_markup=create_keyboard(crops, crop_callback))

def create_keyboard(options, callback):
    markup = InlineKeyboardMarkup()
    for option in options:
        markup.add(InlineKeyboardButton(text=option, callback_data=callback.new(name=option)))
    return markup

@dp.callback_query_handler(crop_callback.filter())
async def select_soil(callback_query: types.CallbackQuery, callback_data: dict):
    crop = callback_data["name"]
    await bot.send_message(callback_query.from_user.id, f"✅ Ви обрали {crop}. Тепер оберіть тип ґрунту:",
                           reply_markup=create_keyboard(soil_types, crop_callback))

# Розрахунок добрив
async def calculate_fertilizer(crop, soil, prev_crop, moisture, yield_goal):
    # Базові норми виносу елементів живлення на 1 т врожаю
    nutrient_needs = {
        "Пшениця": {"N": 30, "P": 12, "K": 25},
        "Кукурудза": {"N": 27, "P": 11, "K": 24},
        "Соняшник": {"N": 50, "P": 15, "K": 60},
        "Ріпак": {"N": 70, "P": 20, "K": 45},
        "Соя": {"N": 40, "P": 10, "K": 30}
    }
    
    # Врахування типу ґрунту
    soil_adjustment = {"Чорнозем": 1.0, "Супіщаний": 1.2, "Глинистий": 0.8}
    
    # Врахування попередника
    prev_crop_adjustment = {"Зернові": 1.1, "Бобові": 0.7, "Технічні": 1.3}
    
    # Кінцеві розрахунки
    n_need = nutrient_needs[crop]["N"] * yield_goal * soil_adjustment[soil] * prev_crop_adjustment[prev_crop]
    p_need = nutrient_needs[crop]["P"] * yield_goal * soil_adjustment[soil] * prev_crop_adjustment[prev_crop]
    k_need = nutrient_needs[crop]["K"] * yield_goal * soil_adjustment[soil] * prev_crop_adjustment[prev_crop]
    
    return {
        "N": round(n_need),
        "P": round(p_need),
        "K": round(k_need),
        "Recommendation": f"Рекомендовані норми: N-{round(n_need)} кг/га, P-{round(p_need)} кг/га, K-{round(k_need)} кг/га"
    }

@dp.callback_query_handler()
async def show_fertilizer_recommendation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    crop, soil, prev_crop, moisture, yield_goal = "Кукурудза", "Чорнозем", "Зернові", "Середня", 6  # Приклад значень
    result = await calculate_fertilizer(crop, soil, prev_crop, moisture, yield_goal)
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💰 Врахувати аналіз ґрунту", callback_data="consider_analysis"),
        InlineKeyboardButton("🔄 Змінити марки добрив", callback_data="change_fertilizer"),
    )
    
    await bot.send_message(user_id, result["Recommendation"], reply_markup=keyboard)

# Обробник кнопки "Врахувати аналіз ґрунту"
@dp.callback_query_handler(lambda c: c.data == "consider_analysis")
async def consider_analysis(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "⚠️ Введіть ваші результати аналізу ґрунту:")

# Запуск бота
if __name__ == "__main__":
    import asyncio
    from aiogram import executor
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
