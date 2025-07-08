# bot.py
import os
import joblib
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

from get_pairs import get_top_pairs
from data_fetch import get_klines, get_price
from features import prepare

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

def analyze(symbol):
    df = get_klines(symbol, limit=500)
    X, _ = prepare(df)
    last = X.iloc[[-1]].values
    pred = model.predict(last)[0]
    prob = model.predict_proba(last)[0][pred]
    price = get_price(symbol)
    sl = price * (0.995 if pred else 1.005)
    tp = price * (1.01 if pred else 0.99)
    direction = "LONG" if pred else "SHORT"
    return {
        "symbol": symbol,
        "direction": direction,
        "price": price,
        "sl": sl,
        "tp": tp,
        "confidence": prob
    }

def select_best_signal():
    best = None
    pairs = get_top_pairs()

    for symbol in pairs:
        try:
            result = analyze(symbol)
            if result["confidence"] > 0.8:  # 80%
                if best is None or result["confidence"] > best["confidence"]:
                    best = result
        except Exception as e:
            print(f"❌ {symbol} error: {e}")
    
    return best

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signal = select_best_signal()
    if signal:
        msg = f"{signal['symbol']}\n{signal['direction']} @ {signal['price']:.4f}\nSL {signal['sl']:.4f} / TP {signal['tp']:.4f}\nConf: {signal['confidence']*100:.1f}%"
    else:
        msg = "⚠️ No high-confidence signals found."
    await update.message.reply_text(msg)

def send_auto_signal():
    bot = Bot(token=TELEGRAM_TOKEN)
    signal = select_best_signal()
    if signal:
        msg = f"{signal['symbol']}\n{signal['direction']} @ {signal['price']:.4f}\nSL {signal['sl']:.4f} / TP {signal['tp']:.4f}\nConf: {signal['confidence']*100:.1f}%"
    else:
        msg = "⚠️ No high-confidence signals found."
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
