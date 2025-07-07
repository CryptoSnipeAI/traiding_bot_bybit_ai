import os
import joblib
import pandas as pd
from data_fetch import get_klines
from features import prepare
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MODELS_DIR = "models"

def analyze(symbol, model):
    df = get_klines(symbol, limit=500)
    X, _ = prepare(df)
    last = X.iloc[[-1]].values
    pred = model.predict(last)[0]
    prob = model.predict_proba(last)[0][pred]
    entry = df['close'].iloc[-1]
    sl = entry * (0.995 if pred else 1.005)
    tp = entry * (1.01 if pred else 0.99)
    return f"{symbol}\n{'LONG' if pred else 'SHORT'} @ {entry:.2f}\nSL {sl:.2f} / TP {tp:.2f}\nConf: {prob*100:.1f}%"

def send_signals():
    bot = Bot(token=TELEGRAM_TOKEN)
    for filename in os.listdir(MODELS_DIR):
        if filename.endswith(".pkl"):
            symbol = filename.replace("_xgb.pkl", "")
            model = joblib.load(os.path.join(MODELS_DIR, filename))
            try:
                msg = analyze(symbol, model)
                bot.send_message(chat_id=CHAT_ID, text=msg)
            except Exception as e:
                print(f"Error with {symbol}: {e}")

def signal_cmd(update, context):
    send_signals()

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("signal", signal_cmd))
    updater.start_polling()
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_signals, 'interval', minutes=15)
    scheduler.start()
    updater.idle()

if __name__ == "__main__":
    main()
