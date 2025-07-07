FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get update && \
    apt-get install -y build-essential libffi-dev libssl-dev libta-lib0 libta-lib0-dev && \
    pip install --no-cache-dir -r requirements.txt

ENV TELEGRAM_TOKEN=your_token
ENV CHAT_ID=your_chat_id

CMD ["python", "bot.py"]
