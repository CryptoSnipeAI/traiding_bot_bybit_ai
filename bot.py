import requests
import pandas as pd
import joblib
from telegram.ext import Updater, CommandHandler
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
from keep_alive import keep_alive

keep_alive()

model = joblib.load("xgboost_model.pkl")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "TONUSDT", "SHIBUSDT", "TRXUSDT", "LTCUSDT",
    "UNIUSDT", "OPUSDT", "ARBUSDT", "APTUSDT", "PEPEUSDT"
]

TELEGRAM_TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = "ТВОЙ_CHAT_ID"

def get_klines(symbol, interval='15', limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    r = requests.get(url, params=params).json()
    data = r['result']['list']
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype(float)
    return df

def analyze(symbol):
    try:
        df = get_klines(symbol)
        df["return"] = df["close"].pct_change()
        df["volatility"] = (df["high"] - df["low"]) / df["open"]
        df["momentum"] = df["close"] - df["close"].rolling(5).mean()
        df = df.dropna()
        X = df[["return", "volatility", "momentum"]].iloc[-1:].values
        pred = model.predict(X)[0]
        prob = model.predict_proba(X)[0][pred]

        entry = df["close"].iloc[-1]
        sl = entry * (0.99 if pred == 1 else 1.01)
        tp = entry * (1.02 if pred == 1 else 0.98)

        return f"{symbol}\nНаправление: {'LONG' if pred == 1 else 'SHORT'}\nВход: {entry:.2f}\nСтоп-лосс: {sl:.2f}\nТейк-профит: {tp:.2f}\nУверенность: {prob*100:.2f}%\n"
    except Exception as e:
        return f"{symbol}: Ошибка - {str(e)}"

def signal(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Анализирую пары...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(analyze, SYMBOLS)
    for result in results:
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def auto_signals():
    bot = Bot(TELEGRAM_TOKEN)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(analyze, SYMBOLS)
    for result in results:
        bot.send_message(chat_id=CHAT_ID, text=result)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("signal", signal))
    updater.start_polling()

    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_signals, 'interval', minutes=15)
    scheduler.start()

    updater.idle()

if __name__ == '__main__':
    main()