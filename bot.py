# bot.py
import os
import joblib
from get_pairs import get_top_pairs
from data_fetch import get_klines
from features import prepare
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
model = joblib.load("model.pkl")


def analyze(symbol):
    df = get_klines(symbol)
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
        "text": f"{symbol}\n{direction} @ {entry:.2f}\nSL {sl:.2f} / TP {tp:.2f}\nConf: {prob*100:.1f}%",
        "confidence": prob
    }

def analyze_best_pair():
    best = {"confidence": 0}
    for symbol in get_top_pairs():
        try:
            result = analyze(symbol)
            if result["confidence"] > best["confidence"] and result["confidence"] >= 0.80:
                best = result
        except Exception as e:
            print(f"❌ {symbol} error: {e}")
    return best.get("text") or "❗️Нет подходящих сигналов с высокой вероятностью."

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = analyze_best_pair()
    await update.message.reply_text(msg)

def send_auto_signal():
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = analyze_best_pair()
    bot.send_message(chat_id=CHAT_ID, text=msg)

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
