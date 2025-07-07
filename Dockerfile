# Используем официальный Python 3.9 образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы в контейнер
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем порт для Flask
EXPOSE 8080

# Команда запуска бота
CMD ["python", "bot.py"]