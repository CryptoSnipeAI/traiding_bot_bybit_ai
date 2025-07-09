# bot.py
import os
import joblib
import pandas as pd
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

from data_fetch import get_klines
from features import prepare
from get_pairs import get_top_pairs

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

def analyze(symbol, model):
    try:
        df = get_klines(symbol, limit=500)
        X, _ = prepare(df)
        last = X.iloc[[-1]].values
        pred = model.predict(last)[0]
        prob = model.predict_proba(last)[0][pred]
        entry = df['close'].iloc[-1]
        sl = entry * (0.995 if pred else 1.005)
        tp = entry * (1.01 if pred else 0.99)
        direction = "LONG" if pred else "SHORT"
        return {
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "conf": prob
        }
    except Exception as e:
        print(f"❌ {symbol} error: {e}")
        return None

def get_best_signal():
    pairs = get_top_pairs()
    best = None

    for symbol in pairs:
        result = analyze(symbol, model)
        if result and result["conf"] > 0.80:  # 80%
            if best is None or result["conf"] > best["conf"]:
                best = result

    return best

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    best = get_best_signal()
    if best:
        msg = f"{best['symbol']}\n{best['direction']} @ {best['entry']:.2f}\nSL {best['sl']:.2f} / TP {best['tp']:.2f}\nConf: {best['conf']*100:.1f}%"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Нет подходящих сигналов.")

def send_auto_signal():
    bot = Bot(token=TELEGRAM_TOKEN)
    best = get_best_signal()
    if best:
        msg = f"{best['symbol']}\n{best['direction']} @ {best['entry']:.2f}\nSL {best['sl']:.2f} / TP {best['tp']:.2f}\nConf: {best['conf']*100:.1f}%"
        bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        bot.send_message(chat_id=CHAT_ID, text="❌ Нет подходящих сигналов.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_cmd))

    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(send_auto_signal, 'interval', minutes=15)
    scheduler.start()

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()

