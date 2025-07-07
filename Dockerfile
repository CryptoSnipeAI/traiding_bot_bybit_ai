FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Скачиваем и компилируем TA-Lib
RUN curl -L http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz | tar -xz && \
    cd ta-lib && \
    ./configure --prefix=/usr/local && \
    make && make install && \
    cd .. && rm -rf ta-lib && \
    echo "/usr/local/lib" >> /etc/ld.so.conf.d/ta-lib.conf && ldconfig

# Указываем путь к библиотеке для pip
ENV TA_LIBRARY_PATH=/usr/local/lib
ENV TA_INCLUDE_PATH=/usr/local/include

COPY . /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV TELEGRAM_TOKEN=your_token
ENV CHAT_ID=your_chat_id

CMD ["python", "bot.py"]
