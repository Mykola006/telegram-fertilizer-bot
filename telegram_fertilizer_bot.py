import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Посилання на сайт
BOT_INFO_URL = "https://sites.google.com/view/agronom-bot/"

# Лічильник безкоштовних розрахунків
user_data = {}

# Основна клавіатура
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🟢 Обрати культуру"),
    KeyboardButton("ℹ️ Інформація про бота")
)

# Варіанти культур
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]

# Попередники
previous_crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя", "Чистий пар"]

# Типи ґрунтів
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for option in options:
        keyboard.add(KeyboardButton(option))
    return keyboard

# Функція клавіатури після розрахунку
def create_post_calc_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Обрати іншу культуру"))
    keyboard.add(KeyboardButton("🔍 Переглянути інші марки добрив"))
    return keyboard

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_data[message.from_user.id] = {"free_used": False}
    await message.answer("Вітаю! Оберіть культуру:", reply_markup=create_keyboard(crops))

@dp.message(lambda message: message.text in crops)
async def select_soil(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["crop"] = message.text
    await message.answer("Оберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

@dp.message(lambda message: message.text in soil_types)
async def select_previous_crop(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["soil"] = message.text
    await message.answer("Оберіть попередню культуру:", reply_markup=create_keyboard(previous_crops))

@dp.message(lambda message: message.text in previous_crops)
async def calculate_fertilizer(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_data and user_data[user_id]["free_used"]:
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Підтвердити оплату (10$)", callback_data="pay"))
        await message.answer("Щоб продовжити розрахунки, необхідно сплатити 10$.", reply_markup=keyboard)
        return
    else:
        user_data[user_id]["free_used"] = True

    crop = user_data[user_id]["crop"]
    soil = user_data[user_id]["soil"]
    prev_crop = message.text

    # Логіка вибору добрив
    if crop in ["Пшениця", "Ячмінь"]:
        npk = "12-24-12"
        nitrogen = "70-120 кг"
    elif crop in ["Кукурудза", "Соняшник"]:
        npk = "10-26-26"
        nitrogen = "90-140 кг"
    elif crop in ["Ріпак", "Соя"]:
        npk = "8-20-30"
        nitrogen = "50-90 кг"
    else:
        npk = "10-26-26"
        nitrogen = "80-130 кг"

    # Вплив типу ґрунту на рекомендації
    if soil == "Піщаний":
        nitrogen = str(int(nitrogen.split("-")[0]) + 10) + "-" + str(int(nitrogen.split("-")[1]) + 10) + " кг"
    elif soil == "Глинистий":
        nitrogen = str(int(nitrogen.split("-")[0]) - 10) + "-" + str(int(nitrogen.split("-")[1]) - 10) + " кг"

    # Вплив попередника на рекомендації
    if prev_crop in ["Соняшник", "Кукурудза"]:
        nitrogen = str(int(nitrogen.split("-")[0]) + 10) + "-" + str(int(nitrogen.split("-")[1]) + 10) + " кг"
    elif prev_crop == "Чистий пар":
        nitrogen = str(int(nitrogen.split("-")[0]) - 10) + "-" + str(int(nitrogen.split("-")[1]) - 10) + " кг"

    recommendation = {
        "NPK": npk,
        "Nitrogen": nitrogen,
        "Cost_per_ha": "120$"
    }

    response = (
        f"✅ **Рекомендації для {crop}**\n\n"
        f"🌱 **Ґрунт:** {soil}\n"
        f"🌾 **Попередня культура:** {prev_crop}\n"
        f"🔹 **Марка добрив:** {recommendation['NPK']}\n"
        f"🔹 **Азот:** {recommendation['Nitrogen']}\n"
        f"💰 **Середня вартість на 1 га:** {recommendation['Cost_per_ha']}\n"
    )

    await message.answer(response, parse_mode="Markdown", reply_markup=create_post_calc_keyboard())

@dp.callback_query(lambda call: call.data == "pay")
async def process_payment(call: types.CallbackQuery):
    await call.message.answer("✅ Оплату підтверджено! Ви можете обрати іншу культуру.", reply_markup=create_keyboard(crops))

@dp.message(lambda message: message.text == "🔄 Обрати іншу культуру")
async def restart_calculation(message: types.Message):
    await message.answer("Оберіть нову культуру:", reply_markup=create_keyboard(crops))

@dp.message(lambda message: message.text == "ℹ️ Інформація про бота")
async def bot_info(message: types.Message):
    await message.answer(f"ℹ️ Детальна інформація про бота доступна тут: {BOT_INFO_URL}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
