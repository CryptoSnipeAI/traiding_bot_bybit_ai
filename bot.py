import os
import joblib
from data_fetch import get_klines
from features import prepare
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

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

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = analyze("BTCUSDT", model)
    await update.message.reply_text(msg)

def send_auto_signal():
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = analyze("BTCUSDT", model)
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
    
