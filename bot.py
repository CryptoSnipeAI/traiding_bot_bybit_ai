import os
import joblib
from data_fetch import get_klines
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
    "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

def analyze_best_pair(model, threshold=0.80):
    best_msg = None
    best_conf = 0

    for symbol in TOP_SYMBOLS:
        try:
            df = get_klines(symbol, limit=500)

            df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
            df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
            df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
            df["volatility"] = (df["high"] - df["low"]) / df["close"]
            df = df.dropna()

            X = df[["rsi", "ema20", "ema50", "volatility", "volume", "close"]]
            last = X.iloc[[-1]].values

            pred = model.predict(last)[0]
            prob = model.predict_proba(last)[0][pred]

            if prob > best_conf and prob >= threshold:
                entry = df["close"].iloc[-1]
                sl = entry * (0.995 if pred else 1.005)
                tp = entry * (1.01 if pred else 0.99)
                direction = "LONG" if pred else "SHORT"
                best_conf = prob
                best_msg = (
                    f"{symbol}\n{direction} @ {entry:.2f}\n"
                    f"SL {sl:.2f} / TP {tp:.2f}\n"
                    f"Conf: {prob*100:.1f}%"
                )
        except Exception as e:
            print(f"[{symbol}] ❌ Ошибка: {e}")

    return best_msg or "❗️Нет подходящих сигналов с высокой вероятностью."

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = analyze_best_pair(model)
    await update.message.reply_text(msg)

def send_auto_signal():
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = analyze_best_pair(model)
    bot.send_message(chat_id=CHAT_ID, text=msg)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_cmd))

    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(send_auto_signal, 'interval', minutes=15)
    scheduler.start()

    print("✅ Bot started and monitoring top 20 pairs")
    app.run_polling()

if __name__ == "__main__":
    main()
