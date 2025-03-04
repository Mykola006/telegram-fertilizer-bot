import os
import telebot
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Введіть культуру для розрахунку добрив.")

@bot.message_handler(func=lambda message: True)
def calculate_fertilizer(message):
    # Тут буде логіка розрахунку добрив
    bot.send_message(message.chat.id, f"Розрахунок для {message.text}: ...")

bot.polling()
