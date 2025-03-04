import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Лічильник безкоштовних розрахунків
user_data = {}

# Посилання на сайт
BOT_INFO_URL = "https://sites.google.com/view/agronom-bot/"

# Основна клавіатура
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🟢 Обрати культуру"),
    KeyboardButton("ℹ️ Інформація про бота")
)

# Варіанти культур
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]

# Функція створення клавіатури для культур
def create_crop_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for crop in crops:
        keyboard.add(KeyboardButton(crop))
    return keyboard

# Функція створення клавіатури після розрахунку
def create_post_calc_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Обрати іншу культуру"))
    keyboard.add(KeyboardButton("🔍 Переглянути інші марки добрив"))
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_data[message.from_user.id] = {"free_used": False}
    await message.answer("Вітаю! Оберіть культуру:", reply_markup=create_crop_keyboard())

@dp.message_handler(lambda message: message.text in crops)
async def calculate_fertilizer(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_data and user_data[user_id]["free_used"]:
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Підтвердити оплату (10$)", callback_data="pay"))
        await message.answer("Щоб продовжити розрахунки, необхідно сплатити 10$.", reply_markup=keyboard)
        return
    else:
        user_data[user_id]["free_used"] = True

    crop = message.text
    # Простий алгоритм розрахунку добрив
    recommendation = {
        "NPK": "10-26-26",
        "Sulfur": "5-10 кг",
        "Nitrogen": "50-100 кг",
        "Cost_per_ha": "120$"
    }
    
    response = (
        f"✅ **Рекомендації для {crop}**\n\n"
        f"🔹 **Марка добрив:** {recommendation['NPK']}\n"
        f"🔹 **Сірка:** {recommendation['Sulfur']}\n"
        f"🔹 **Азот:** {recommendation['Nitrogen']}\n"
        f"💰 **Середня вартість на 1 га:** {recommendation['Cost_per_ha']}\n"
    )

    await message.answer(response, parse_mode="Markdown", reply_markup=create_post_calc_keyboard())

@dp.callback_query_handler(lambda call: call.data == "pay")
async def process_payment(call: types.CallbackQuery):
    await call.message.answer("✅ Оплату підтверджено! Ви можете обрати іншу культуру.", reply_markup=create_crop_keyboard())

@dp.message_handler(lambda message: message.text == "🔄 Обрати іншу культуру")
async def restart_calculation(message: types.Message):
    await message.answer("Оберіть нову культуру:", reply_markup=create_crop_keyboard())

@dp.message_handler(lambda message: message.text == "ℹ️ Інформація про бота")
async def bot_info(message: types.Message):
    await message.answer(f"ℹ️ Детальна інформація про бота доступна тут: {BOT_INFO_URL}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
