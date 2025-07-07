FROM python:3.10-slim

WORKDIR /app

# Установим нужные библиотеки и инструменты для сборки
RUN apt-get update && \
    apt-get install -y build-essential wget curl unzip git \
                       libffi-dev libssl-dev \
                       python3-dev

# Скачиваем и компилируем TA-Lib из исходников
RUN curl -L http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz | tar -xz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && rm -rf ta-lib

# Копируем проект
COPY . /app

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Объявляем переменные окружения (можешь переопределить в docker-compose.yml)
ENV TELEGRAM_TOKEN=your_token
ENV CHAT_ID=your_chat_id

CMD ["python", "bot.py"]
