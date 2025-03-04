import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Варіанти вибору
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Орієнтовні потреби культур у NPK (на 1 ц врожаю)
crop_requirements = {
    "Пшениця": {"N": 2.5, "P": 1.2, "K": 2.0},
    "Кукурудза": {"N": 2.8, "P": 1.0, "K": 2.5},
    "Соняшник": {"N": 3.0, "P": 1.5, "K": 3.5},
    "Ріпак": {"N": 3.2, "P": 1.8, "K": 2.8},
    "Ячмінь": {"N": 2.3, "P": 1.1, "K": 1.8},
    "Соя": {"N": 4.0, "P": 1.6, "K": 2.2},
}

# Середній вміст елементів у ґрунті (кг/га)
soil_npk = {
    "Чорнозем": {"N": 60, "P": 40, "K": 180},
    "Сірозем": {"N": 40, "P": 30, "K": 150},
    "Піщаний": {"N": 30, "P": 20, "K": 100},
    "Глинистий": {"N": 50, "P": 35, "K": 170},
    "Супіщаний": {"N": 35, "P": 25, "K": 120},
}

# Вплив попередника (на зниження потреби у NPK)
previous_crop_factor = {
    "Зернові": {"N": 1.0, "P": 1.0, "K": 1.0},
    "Бобові": {"N": 0.8, "P": 1.0, "K": 1.0},
    "Технічні": {"N": 1.1, "P": 1.2, "K": 1.1},
    "Овочі": {"N": 1.2, "P": 1.3, "K": 1.2},
    "Чистий пар": {"N": 0.9, "P": 1.0, "K": 1.0},
}

# Збереження вибору користувача
user_selection = {}

# Функція створення клавіатури
def create_keyboard(options):
    keyboard = [[KeyboardButton(text=option)] for option in options]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Обробник команди /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_selection[message.chat.id] = {}
    await message.answer("Вітаю! Оберіть культуру:", reply_markup=create_keyboard(crops))

# Обробники вибору
@dp.message()
async def handle_message(message: Message):
    user_id = message.chat.id
    text = message.text

    if text in crops:
        user_selection[user_id]["crop"] = text
        await message.answer(f"Ви обрали культуру: <b>{text}</b>. Введіть планову врожайність у ц/га:")

    elif text.isdigit():
        user_selection[user_id]["yield"] = int(text)
        await message.answer("Тепер виберіть тип ґрунту:", reply_markup=create_keyboard(soil_types))

    elif text in soil_types:
        user_selection[user_id]["soil"] = text
        await message.answer("Тепер виберіть попередник:", reply_markup=create_keyboard(previous_crops))

    elif text in previous_crops:
        user_selection[user_id]["previous_crop"] = text
        await message.answer("Тепер виберіть зону зволоження:", reply_markup=create_keyboard(moisture_zones))

    elif text in moisture_zones:
        user_selection[user_id]["moisture"] = text

        # Отримуємо дані
        crop = user_selection[user_id]["crop"]
        planned_yield = user_selection[user_id]["yield"]
        soil = user_selection[user_id]["soil"]
        prev_crop = user_selection[user_id]["previous_crop"]

        # Базова потреба в добривах
        n_need = crop_requirements[crop]["N"] * planned_yield
        p_need = crop_requirements[crop]["P"] * planned_yield
        k_need = crop_requirements[crop]["K"] * planned_yield

        # Віднімаємо середній запас елементів у ґрунті
        n_need -= soil_npk[soil]["N"]
        p_need -= soil_npk[soil]["P"]
        k_need -= soil_npk[soil]["K"]

        # Враховуємо попередник
        n_need *= previous_crop_factor[prev_crop]["N"]
        p_need *= previous_crop_factor[prev_crop]["P"]
        k_need *= previous_crop_factor[prev_crop]["K"]

        # Підбір добрив
        fertilizer_plan = (
            f"✅ Основне внесення: NPK 10-26-26 - {round(p_need * 2, 1)} кг/га\n"
            f"🔹 Передпосівне удобрення: NPK 16-16-16 - {round((p_need + k_need) * 1.5, 1)} кг/га\n"
            f"🌱 Підживлення азотом: КАС 32% - {round(n_need / 2, 1)} кг/га\n"
        )

        await message.answer(f"📌 <b>Рекомендація:</b>\n{fertilizer_plan}", parse_mode="HTML")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
