import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Фінансовий ліміт на безкоштовний розрахунок
FREE_LIMIT = 1
user_usage = {}

# Стани для опрацювання введених даних
class FertilizerForm(StatesGroup):
    crop = State()
    soil_type = State()
    prev_crop = State()
    yield_goal = State()

# Головне меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🌱 Обрати культуру")],
        [KeyboardButton("ℹ️ Інформація про бота")]
    ],
    resize_keyboard=True
)

# Функція обробки старту
@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=main_menu)
    await state.clear()

# Вибір культури
@dp.message_handler(lambda message: message.text == "🌱 Обрати культуру")
async def select_crop(message: types.Message, state: FSMContext):
    crops = ["Кукурудза", "Пшениця", "Соняшник", "Ріпак"]
    crop_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for crop in crops:
        crop_kb.add(KeyboardButton(crop))
    await message.answer("Будь ласка, оберіть культуру:", reply_markup=crop_kb)
    await state.set_state(FertilizerForm.crop)

# Обробка вибору культури
@dp.message_handler(state=FertilizerForm.crop)
async def process_crop(message: types.Message, state: FSMContext):
    await state.update_data(crop=message.text)
    soils = ["Чорнозем", "Супіщаний", "Глинистий"]
    soil_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for soil in soils:
        soil_kb.add(KeyboardButton(soil))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть тип ґрунту:", reply_markup=soil_kb)
    await state.set_state(FertilizerForm.soil_type)

# Обробка вибору ґрунту
@dp.message_handler(state=FertilizerForm.soil_type)
async def process_soil(message: types.Message, state: FSMContext):
    await state.update_data(soil_type=message.text)
    prev_crops = ["Бобові", "Зернові", "Технічні", "Овочі"]
    prev_crop_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for prev in prev_crops:
        prev_crop_kb.add(KeyboardButton(prev))
    await message.answer(f"✅ Ви обрали {message.text}. Тепер оберіть попередник:", reply_markup=prev_crop_kb)
    await state.set_state(FertilizerForm.prev_crop)

# Обробка попередника
@dp.message_handler(state=FertilizerForm.prev_crop)
async def process_prev_crop(message: types.Message, state: FSMContext):
    await state.update_data(prev_crop=message.text)
    await message.answer("Введіть планову врожайність у ц/га (наприклад, 80):")
    await state.set_state(FertilizerForm.yield_goal)

# Розрахунок добрив
@dp.message_handler(state=FertilizerForm.yield_goal)
async def process_yield_goal(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    crop = user_data['crop']
    soil_type = user_data['soil_type']
    prev_crop = user_data['prev_crop']
    try:
        yield_goal = int(message.text)
    except ValueError:
        await message.answer("Будь ласка, введіть числове значення.")
        return
    
    # Логіка підбору добрив
    recommendation = {
        "Комплексні добрива": "NPK 16-16-16 - 250 кг/га",
        "Азотні": "КАС-32 - 100 кг/га",
        "Сірчані": "Сульфат амонію - 80 кг/га",
        "Орієнтовна вартість": "120$/га"
    }
    
    response = f"📊 Рекомендації для {crop} ({yield_goal} ц/га)\n"
    response += f"🟢 Комплексні: {recommendation['Комплексні добрива']}\n"
    response += f"🔵 Азотні: {recommendation['Азотні']}\n"
    response += f"🟡 Сірчані: {recommendation['Сірчані']}\n"
    response += f"💲 Вартість: {recommendation['Орієнтовна вартість']}\n"
    
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Змінити марки добрив", callback_data="change_fertilizers")],
            [InlineKeyboardButton(text="💰 Врахувати аналіз ґрунту", callback_data="paid_analysis")]
        ]
    )
    await message.answer(response, reply_markup=buttons)
    await state.clear()

# Реакція на кнопки
@dp.callback_query_handler(lambda c: c.data == "change_fertilizers")
async def change_fertilizers(callback: types.CallbackQuery):
    await callback.message.answer("⚙ Оновлення списку добрив... (функція в розробці)")

@dp.callback_query_handler(lambda c: c.data == "paid_analysis")
async def paid_analysis(callback: types.CallbackQuery):
    await callback.message.answer("💰 Врахування аналізу ґрунту можливе після оплати (функція в розробці).")

if __name__ == "__main__":
    import asyncio
    from aiogram import executor
    asyncio.run(dp.start_polling(bot))
