import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавіатури
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌱 Обрати культуру")],
        [KeyboardButton(text="ℹ️ Інформація про бота")]
    ],
    resize_keyboard=True
)

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Обрати іншу культуру")],
        [KeyboardButton(text="⚙️ Альтернативні варіанти живлення")]
    ],
    resize_keyboard=True
)

# Інлайн-кнопка для умовної оплати
payment_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💳 Отримати детальний розрахунок (10$)", callback_data="pay")]
    ]
)

# Всі культури та типи ґрунтів
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Підзолистий", "Глинистий", "Супіщаний"]
previous_crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]

# Головний обробник команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Вітаю! Це бот для розрахунку мінерального живлення. Оберіть культуру:", reply_markup=main_keyboard)

# Обробка вибору культури
@dp.message(lambda message: message.text in crops)
async def select_crop(message: types.Message):
    selected_crop = message.text
    await message.answer(f"✅ Ви обрали {selected_crop}. Тепер оберіть тип ґрунту:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=soil)] for soil in soil_types],
        resize_keyboard=True
    ))

# Обробка вибору ґрунту
@dp.message(lambda message: message.text in soil_types)
async def select_soil(message: types.Message):
    selected_soil = message.text
    await message.answer(f"✅ Ви обрали {selected_soil}. Тепер оберіть попередник:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=prev)] for prev in previous_crops],
        resize_keyboard=True
    ))

# Обробка вибору попередника
@dp.message(lambda message: message.text in previous_crops)
async def select_previous_crop(message: types.Message):
    selected_previous_crop = message.text
    await message.answer(f"✅ Ви обрали {selected_previous_crop}. Розрахунок живлення...", reply_markup=types.ReplyKeyboardRemove())
    
    # Генерація рекомендацій
    recommendation = generate_fertilizer_recommendation(selected_previous_crop)
    
    await message.answer(f"💡 Рекомендація для {selected_previous_crop}:\n\n"
                         f"📌 Комплексне добриво: {recommendation['complex_fertilizer']}, {recommendation['complex_rate']} кг/га\n"
                         f"📌 Азотні добрива: {recommendation['nitrogen_fertilizer']}, {recommendation['nitrogen_rate']} кг/га\n"
                         f"📌 Сірчані добрива: {recommendation['sulfur_fertilizer']}, {recommendation['sulfur_rate']} кг/га\n"
                         f"💰 Орієнтовна вартість: {recommendation['cost']}$/га", reply_markup=back_keyboard)

# Генерація рекомендацій на основі культури, ґрунту і попередника
def generate_fertilizer_recommendation(previous_crop):
    fertilizer_data = {
        "Пшениця": {"complex_fertilizer": "NPK 10-26-26", "complex_rate": 150, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 100, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 50, "cost": 120},
        "Кукурудза": {"complex_fertilizer": "NPK 15-15-15", "complex_rate": 200, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 120, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 40, "cost": 150},
        "Соняшник": {"complex_fertilizer": "NPK 12-24-12", "complex_rate": 180, "nitrogen_fertilizer": "Карбамід", "nitrogen_rate": 90, "sulfur_fertilizer": "Сульфат амонію", "sulfur_rate": 60, "cost": 130},
    }
    return fertilizer_data.get(previous_crop, fertilizer_data["Пшениця"])

# Оплата
@dp.callback_query(lambda c: c.data == "pay")
async def process_payment(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "💳 Для отримання повного аналізу натисніть кнопку нижче:", reply_markup=payment_button)

# Обробка натискання "Інформація про бота"
@dp.message(lambda message: message.text == "ℹ️ Інформація про бота")
async def bot_info(message: types.Message):
    await message.answer("ℹ️ Дізнайтесь більше про нашого бота тут: [Агроном у смартфоні](https://sites.google.com/view/agronom-bot/)", parse_mode="Markdown")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
