# bot.py
import os
import joblib
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


def analyze(symbol):
    df = get_klines(symbol, limit=500)
    X, _ = prepare(df)
    last = X.iloc[[-1]].values
    pred = model.predict(last)[0]
    prob = model.predict_proba(last)[0][pred]
    entry = df['close'].iloc[-1]
    sl = entry * (0.995 if pred else 1.005)
    tp = entry * (1.01 if pred else 0.99)
    direction = "LONG" if pred else "SHORT"
    return symbol, prob, f"{symbol}\n{direction} @ {entry:.2f}\nSL {sl:.2f} / TP {tp:.2f}\nConf: {prob*100:.1f}%"


def find_best_signal():
    best = (None, 0, None)
    for symbol in get_top_pairs():
        try:
            sym, prob, msg = analyze(symbol)
            print(f"✅ {symbol}: {prob:.2f}")
            if prob > best[1]:
                best = (sym, prob, msg)
        except Exception as e:
            print(f"❌ {symbol} error: {e}")
    return best[2] if best[2] else "Нет подходящих сигналов."


async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = find_best_signal()
    await update.message.reply_text(msg)


def send_auto_signal():
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = find_best_signal()
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
