import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types.input_file import InputFile
import pdfkit
import os
from dotenv import load_dotenv

# Завантаження токену з .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логування
logging.basicConfig(level=logging.INFO)

# Перевіряємо встановлення wkhtmltopdf
WKHTMLTOPDF_PATH = "/usr/bin/wkhtmltopdf"  # Шлях може відрізнятись у залежності від сервера
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# Класи станів для фінансових розрахунків
class FertilizerCalculation(StatesGroup):
    crop = State()
    yield_goal = State()
    area = State()
    soil_type = State()

# Функція для розрахунку добрив
async def calculate_fertilizer(crop, yield_goal, area, soil_type):
    nutrient_requirements = {
        "пшениця": {"N": 30, "P": 10, "K": 20},
        "кукурудза": {"N": 25, "P": 12, "K": 25},
        "соняшник": {"N": 42, "P": 18, "K": 85},
        "соя": {"N": 15, "P": 20, "K": 30},
        "ріпак": {"N": 50, "P": 15, "K": 40}
    }
    
    if crop not in nutrient_requirements:
        return "Помилка: невідома культура."
    
    needs = nutrient_requirements[crop]
    n_fertilizer = needs["N"] * yield_goal * area
    p_fertilizer = needs["P"] * yield_goal * area
    k_fertilizer = needs["K"] * yield_goal * area
    
    return f"🔹 Для {crop} на площі {area} га з метою {yield_goal} т/га:\n"            f"    - Азот (N): {n_fertilizer} кг\n"            f"    - Фосфор (P): {p_fertilizer} кг\n"            f"    - Калій (K): {k_fertilizer} кг"

# Функція формування PDF
async def generate_pdf(data):
    filename = "recommendation.pdf"
    html = f"<html><body><h2>Рекомендації по живленню</h2><p>{data}</p></body></html>"
    pdfkit.from_string(html, filename, configuration=config)
    return filename

# Команда старт
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Розрахунок добрив", callback_data="calc_fertilizer")],
        [InlineKeyboardButton(text="🌱 Довідник культур", callback_data="crop_guide")],
        [InlineKeyboardButton(text="📄 Отримати PDF", callback_data="get_pdf")]
    ])
    await message.answer("Вітаю! Я бот-агроном. Оберіть дію:", reply_markup=keyboard)

# Обробник розрахунку добрив
@dp.callback_query(lambda c: c.data == "calc_fertilizer")
async def ask_crop(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(FertilizerCalculation.crop)
    await callback_query.message.answer("🌾 Введіть культуру (пшениця, кукурудза, соняшник, соя, ріпак):")

@dp.message(FertilizerCalculation.crop)
async def ask_yield_goal(message: types.Message, state: FSMContext):
    await state.update_data(crop=message.text.lower())
    await state.set_state(FertilizerCalculation.yield_goal)
    await message.answer("📊 Введіть очікувану врожайність (т/га):")

@dp.message(FertilizerCalculation.yield_goal)
async def ask_area(message: types.Message, state: FSMContext):
    await state.update_data(yield_goal=float(message.text))
    await state.set_state(FertilizerCalculation.area)
    await message.answer("📏 Введіть площу поля (га):")

@dp.message(FertilizerCalculation.area)
async def ask_soil_type(message: types.Message, state: FSMContext):
    await state.update_data(area=float(message.text))
    await state.set_state(FertilizerCalculation.soil_type)
    await message.answer("🟤 Введіть тип ґрунту (чорнозем, супіщаний, глинистий):")

@dp.message(FertilizerCalculation.soil_type)
async def show_result(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    crop = user_data["crop"]
    yield_goal = user_data["yield_goal"]
    area = user_data["area"]
    soil_type = message.text.lower()
    
    result = await calculate_fertilizer(crop, yield_goal, area, soil_type)
    await message.answer(result)
    await state.clear()

# Обробник генерації PDF
@dp.callback_query(lambda c: c.data == "get_pdf")
async def send_pdf(callback_query: types.CallbackQuery):
    pdf_file = await generate_pdf("Приклад рекомендацій по живленню")
    await bot.send_document(callback_query.from_user.id, InputFile(pdf_file))

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
