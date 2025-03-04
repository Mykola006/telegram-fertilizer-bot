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

# Список культур, типів ґрунту, попередників
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Супіщаний", "Глинистий", "Підзолистий"]
previous_crops = ["Зернові", "Бобові", "Олійні"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Додаткові параметри
price_per_kg = {"N": 0.8, "P": 1.2, "K": 1.0}  # Ціни на добрива
base_yield = 6.0  # Базова врожайність у т/га

def adjust_for_soil_analysis(fertilizer_rates, soil_analysis):
    return {key: max(0, fertilizer_rates[key] - soil_analysis.get(key, 0)) for key in fertilizer_rates}

def adjust_for_yield(fertilizer_rates, planned_yield):
    factor = planned_yield / base_yield
    return {key: round(fertilizer_rates[key] * factor) for key in fertilizer_rates}

def split_fertilization(fertilizer_rates):
    return {
        "Основне внесення": {key: round(fertilizer_rates[key] * 0.5) for key in fertilizer_rates},
        "Передпосівне": {key: round(fertilizer_rates[key] * 0.3) for key in fertilizer_rates},
        "Підживлення": {key: round(fertilizer_rates[key] * 0.2) for key in fertilizer_rates}
    }

def calculate_fertilizer_cost(fertilizer_rates):
    return sum(fertilizer_rates[element] * price_per_kg[element] for element in ["N", "P", "K"])

def adjust_for_soil_ph(soil_ph, target_ph=6.5):
    if soil_ph < target_ph:
        return f"Рекомендується внесення вапна: {round((target_ph - soil_ph) * 2, 1)} т/га"
    return "pH ґрунту в нормі, вапнування не потрібне."

def check_climate_risks(moisture):
    if moisture == "Низька":
        return "⚠️ Ризик низької ефективності добрив через нестачу вологи! Рекомендується дробове внесення."
    return "✅ Оптимальні умови для внесення добрив."

def optimize_fertilizer_budget(fertilizer_rates, budget):
    total_cost = calculate_fertilizer_cost(fertilizer_rates)
    if total_cost > budget:
        factor = budget / total_cost
        return {key: round(fertilizer_rates[key] * factor) for key in fertilizer_rates}
    return fertilizer_rates

@dp.message(lambda message: message.text in moisture_zones)
async def calculate_fertilizers(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if not all(key in user_data for key in ["crop", "soil", "previous_crop"]):
        await message.answer("⚠️ Виникла помилка! Почніть спочатку.")
        return
    
    crop, soil, prev_crop, moisture = user_data["crop"], user_data["soil"], user_data["previous_crop"], message.text
    fertilizer_rates = calculate_fertilizer(crop, soil, prev_crop, moisture)
    fertilizer_rates = adjust_for_soil_analysis(fertilizer_rates, soil_analysis)
    fertilizer_rates = adjust_for_yield(fertilizer_rates, planned_yield)
    fertilizer_rates = optimize_fertilizer_budget(fertilizer_rates, budget)

    fertilization_plan = split_fertilization(fertilizer_rates)
    ph_recommendation = adjust_for_soil_ph(soil_ph)
    climate_warning = check_climate_risks(moisture)

    total_cost = calculate_fertilizer_cost(fertilizer_rates)

    response = f"""
🔍 **Аналітичні дані**:
🌾 Культура: {crop}
🪵 Попередник: {prev_crop}
🌍 Тип ґрунту: {soil}
💧 Зона зволоження: {moisture}
📊 **Рекомендовані добрива (кг/га)**: {fertilization_plan}
💰 **Орієнтовна вартість**: {total_cost} $/га
⚠️ {ph_recommendation}
⚠️ {climate_warning}
"""
    await message.answer(response)

if __name__ == "__main__":
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
