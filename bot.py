import os
import joblib
import pandas as pd
from data_fetch import get_klines
from features import prepare
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN and CHAT_ID must be set as environment variables.")

def analyze(symbol, model):
    df = get_klines(symbol, limit=500)
    X, _ = prepare(df)
    last = X.iloc[[-1]].values
    pred = model.predict(last)[0]
    prob = model.predict_proba(last)[0][pred]
    entry = df['close'].iloc[-1]
    sl = entry * (0.995 if pred else 1.005)
    tp = entry * (1.01 if pred else 0.99)
    direction = "LONG" if pred else "SHORT"
    return f"{symbol}\n{direction} @ {entry:.2f}\nSL {sl:.2f} / TP {tp:.2f}\nConf: {prob*100:.1f}%"

def send_signals():
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        model = joblib.load("model.pkl")  # Загружаем одну модель
        msg = analyze("BTCUSDT", model)   # Укажи нужный символ здесь
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Error: {e}")

def signal_cmd(update, context):
    send_signals()

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("signal", signal_cmd))
    updater.start_polling()

    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(send_signals, 'interval', minutes=15)
    scheduler.start()

    updater.idle()

if __name__ == "__main__":
    main()
