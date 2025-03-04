FROM python:3.10

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

# Додай цю команду для перевірки
RUN ls -lah /app

CMD ["python", "/app/telegram_fertilizer_bot.py"]
