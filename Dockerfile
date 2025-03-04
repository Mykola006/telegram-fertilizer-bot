# Вибираємо базовий образ Python
FROM python:3.11

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли бота в контейнер
COPY . /app

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Встановлюємо змінну середовища для Telegram Token
ENV TOKEN=${TOKEN}

# Запускаємо бота
CMD ["python", "telegram_fertilizer_bot.py"]
