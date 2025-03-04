import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
from aiohttp import web

# Завантаження змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Помилка: TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/{TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Ініціалізація бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Клавіатура головного меню
main_keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
main_keyboard.add(KeyboardButton("\U0001F331 Обрати культуру"))
main_keyboard.add(KeyboardButton("ℹ️ Інформація про бота"))

# Список культур, типів ґрунту, попередників
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий"]
previous_crops = ["Зернові", "Бобові", "Олійні"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Додаткові коефіцієнти для покращеної моделі
fertilizer_data = {
    "Пшениця": {"N": 120, "P": 60, "K": 90, "yield_factor": 1.1},
    "Кукурудза": {"N": 150, "P": 80, "K": 100, "yield_factor": 1.2},
    "Соняшник": {"N": 90, "P": 50, "K": 70, "yield_factor": 1.0},
}

soil_adjustments = {
    "Чорнозем": {"N": 1.0, "P": 1.0, "K": 1.0},
    "Супіщаний": {"N": 1.2, "P": 1.1, "K": 1.2},
    "Глинистий": {"N": 0.9, "P": 1.0, "K": 0.9},
}

prev_crop_adjustments = {
    "Зернові": {"N": 1.1, "P": 1.0, "K": 1.0},
    "Бобові": {"N": 0.8, "P": 1.1, "K": 1.1},
    "Олійні": {"N": 1.0, "P": 1.0, "K": 1.0},
}

moisture_adjustments = {
    "Низька": {"N": 0.9, "P": 1.0, "K": 1.0},
    "Середня": {"N": 1.0, "P": 1.0, "K": 1.0},
    "Достатня": {"N": 1.1, "P": 1.1, "K": 1.1},
}

def calculate_fertilizer(crop, soil, prev_crop, moisture):
    if crop in fertilizer_data:
        base = fertilizer_data[crop]
        n = base["N"] * soil_adjustments[soil]["N"] * prev_crop_adjustments[prev_crop]["N"] * moisture_adjustments[moisture]["N"]
        p = base["P"] * soil_adjustments[soil]["P"] * prev_crop_adjustments[prev_crop]["P"] * moisture_adjustments[moisture]["P"]
        k = base["K"] * soil_adjustments[soil]["K"] * prev_crop_adjustments[prev_crop]["K"] * moisture_adjustments[moisture]["K"]
        return {"N": round(n), "P": round(p), "K": round(k)}
    return None

@dp.message(lambda message: message.text in moisture_zones)
async def calculate_fertilizers(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if not all(key in user_data for key in ["crop", "soil", "previous_crop"]):
        await message.answer("⚠️ Виникла помилка! Почніть спочатку.", reply_markup=main_keyboard)
        return
    
    crop, soil, prev_crop, moisture = user_data["crop"], user_data["soil"], user_data["previous_crop"], message.text
    fert = calculate_fertilizer(crop, soil, prev_crop, moisture)
    if not fert:
        await message.answer("⚠️ Дані для цієї культури не знайдені.")
        return
    
    response = (f"🔍 **Аналітичні дані**:
"
                f"🌾 Культура: {crop}\n"
                f"🪵 Попередник: {prev_crop}\n"
                f"🌍 Тип ґрунту: {soil}\n"
                f"💧 Зона зволоження: {moisture}\n\n"
                f"📊 **Рекомендовані добрива (кг/га)**:\n"
                f"✔ Азот (N): {fert['N']} кг\n"
                f"✔ Фосфор (P): {fert['P']} кг\n"
                f"✔ Калій (K): {fert['K']} кг")
    
    keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
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
