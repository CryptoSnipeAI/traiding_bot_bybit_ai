import time
import telebot
from pybit.unified_trading import HTTP
import config
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
import pandas as pd

bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
session = HTTP(api_key=config.API_KEY, api_secret=config.API_SECRET)

def get_symbols():
    markets = session.get_tickers(category="linear")["result"]["list"]
    return [m["symbol"] for m in markets if "USDT" in m["symbol"]]

def get_klines(symbol):
    try:
        candles = session.get_kline(category="linear", symbol=symbol, interval=15, limit=100)["result"]["list"]
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.astype(float)
        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

def analyze(df):
    rsi = RSIIndicator(close=df["close"]).rsi().iloc[-1]
    ema_fast = EMAIndicator(close=df["close"], window=9).ema_indicator().iloc[-1]
    ema_slow = EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1]
    macd = MACD(close=df["close"]).macd_diff().iloc[-1]

    if rsi < 30 and ema_fast > ema_slow and macd > 0:
        return "long", 90
    elif rsi > 70 and ema_fast < ema_slow and macd < 0:
        return "short", 90
    else:
        return None, 0

def send_signal(symbol, direction, confidence, price):
    tp = round(price * config.TAKE_PROFIT_MULTIPLIER if direction == "long" else price / config.TAKE_PROFIT_MULTIPLIER, 2)
    sl = round(price / config.STOP_LOSS_MULTIPLIER if direction == "long" else price * config.STOP_LOSS_MULTIPLIER, 2)

    message = f"""
Сигнал на {direction.upper()}

Пара: {symbol}
Цена входа: {price}
Плечо: x{config.LEVERAGE}
Стоп-лосс: {sl}
Тейк-профит: {tp}
Уверенность сигнала: {confidence}%

Время сигнала: {time.strftime('%H:%M:%S')}
    """
    bot.send_message(config.TELEGRAM_CHAT_ID, message)

def main():
    while True:
        symbols = get_symbols()
        for symbol in symbols:
            df = get_klines(symbol)
            if df is None or df.empty:
                continue

            direction, confidence = analyze(df)
            if direction and confidence >= config.CONFIDENCE_THRESHOLD:
                current_price = df["close"].iloc[-1]
                send_signal(symbol, direction, confidence, current_price)

        time.sleep(300)

if __name__ == "__main__":
    main()