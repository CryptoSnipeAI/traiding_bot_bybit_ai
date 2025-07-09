# bot.py
import os
import joblib
from data_fetch import get_klines
from features import prepare_features  # Импортируй подготовку с новыми признаками
from get_pairs import get_top_pairs
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

def get_current_price(symbol):
    url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
    resp = requests.get(url).json()
    try:
        return float(resp['result']['list'][0]['lastPrice'])
    except Exception as e:
        print(f"Ошибка получения цены для {symbol}: {e}")
        return None

def analyze(symbol, model):
    df = get_klines(symbol, limit=500)
    df = prepare_features(df)
    last = df.iloc[[-1]][["rsi", "stoch_rsi", "ema20", "ema50", "macd", "macd_signal", "atr", "volatility", "volume", "close"]].values
    pred = model.predict(last)[0]
    prob = max(model.predict_proba(last)[0])

    entry = get_current_price(symbol)
    if entry is None:
        entry = df["close"].iloc[-1]

    sl = entry * (0.995 if pred == 1 else 1.005)
    tp = entry * (1.01 if pred == 1 else 0.99)
    direction = "LONG" if pred == 1 else "SHORT" if pred == 2 else "NO SIGNAL"
    if direction == "NO SIGNAL":
        return None

    return f"{symbol}\n{direction} @ {entry:.4f}\nSL {sl:.4f} / TP {tp:.4f}\nConf: {prob*100:.1f}%"

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = get_top_pairs()
    best_signal = None
    best_prob = 0
    best_symbol = None

    for symbol in pairs:
        try:
            msg = analyze(symbol, model)
            if msg is None:
                continue
            prob = float(msg.split("Conf: ")[1].replace("%", ""))
            if prob > best_prob:
                best_prob = prob
                best_signal = msg
                best_symbol = symbol
        except Exception as e:
            print(f"❌ {symbol} error: {e}")

    if best_signal:
        await update.message.reply_text(best_signal)
    else:
        await update.message.reply_text("Нет подходящих сигналов на данный момент.")

def send_auto_signal():
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    pairs = get_top_pairs()
    best_signal = None
    best_prob = 0

    for symbol in pairs:
        try:
            msg = analyze(symbol, model)
            if msg is None:
                continue
            prob = float(msg.split("Conf: ")[1].replace("%", ""))
            if prob > best_prob:
                best_prob = prob
                best_signal = msg
        except Exception as e:
            print(f"❌ {symbol} error: {e}")

    if best_signal:
        bot.send_message(chat_id=CHAT_ID, text=best_signal)

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
