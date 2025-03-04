from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import logging
import asyncio
import os

# Токен бота (отримується з змінного середовища)
TOKEN = os.getenv("TOKEN")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = dp  # Використовуємо router для обробки команд
logging.basicConfig(level=logging.INFO)

# Кнопки для вибору культури
kb_cultures = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Озимий ріпак")],
        [KeyboardButton(text="Озима пшениця")],
        [KeyboardButton(text="Кукурудза")],
        [KeyboardButton(text="Соняшник")],
        [KeyboardButton(text="Соя")]
    ],
    resize_keyboard=True
)

# База даних норм добрив (NPKS на 1 тону врожаю)
fertilizer_data = {
    "Озимий ріпак": [55, 22, 50, 17],
    "Озима пшениця": [28, 11, 22, 4],
    "Кукурудза": [26, 11, 27, 5],
    "Соняшник": [45, 18, 57, 8],
    "Соя": [75, 18, 38, 7]
}

# Змінна для тимчасового збереження вибору
user_data = {}

@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привіт! Я бот-калькулятор добрив. Обери культуру:", reply_markup=kb_cultures)

@router.message(lambda message: message.text in fertilizer_data.keys())
async def ask_yield(message: types.Message):
    user_data[message.from_user.id] = {"culture": message.text}
    await message.answer("Введіть заплановану врожайність (т/га):")

@router.message(lambda message: message.text.replace('.', '', 1).isdigit())
async def calculate_fertilizer(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        culture = user_data[user_id]["culture"]
        yield_value = float(message.text)
        npks = fertilizer_data[culture]
        
        # Розрахунок потреби в добривах
        n = round(npks[0] * yield_value, 2)
        p = round(npks[1] * yield_value, 2)
        k = round(npks[2] * yield_value, 2)
        s = round(npks[3] * yield_value, 2)
        
        response = (f"Розрахунок для {culture} з врожайністю {yield_value} т/га:\n"
                    f"Азот (N): {n} кг/га\n"
                    f"Фосфор (P₂O₅): {p} кг/га\n"
                    f"Калій (K₂O): {k} кг/га\n"
                    f"Сірка (S): {s} кг/га")
        
        await message.answer(response)
    else:
        await message.answer("Будь ласка, спочатку оберіть культуру.")

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
