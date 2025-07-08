FROM python:3.10-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем проект
COPY . /app

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Переменные окружения для Telegram
ENV TELEGRAM_TOKEN=your_token
ENV CHAT_ID=your_chat_id

# Запуск бота
CMD ["bash", "-c", "python train_model.py && python bot.py"]
