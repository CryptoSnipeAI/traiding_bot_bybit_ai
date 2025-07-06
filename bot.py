import time
import requests
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from telegram import Bot
import config

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

def get_symbols():
    try:
        url = "https://api.bybit.com/v5/market/instruments?category=linear"
        response = requests.get(url)
        data = response.json()
        symbols = [item["symbol"] for item in data["result"]["list"] if item["symbol"].endswith("USDT")]
        return symbols
    except Exception as e:
        print(f"Ошибка при получении списка пар: {e}")
        return []
        
def get_klines(symbol):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=15&limit=100"
        response = requests.get(url)
        data = response.json()["result"]["list"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
        df = df.astype({"close": float, "high": float, "low": float, "volume": float})
        return df
    except Exception as e:
        print(f"Ошибка при получении свечей {symbol}: {e}")
        return None

def analyze(df):
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["ema_9"] = EMAIndicator(df["close"], window=9).ema_indicator()
    df["ema_21"] = EMAIndicator(df["close"], window=21).ema_indicator()
    df["ema_50"] = EMAIndicator(df["close"], window=50).ema_indicator()
    df["atr"] = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"]).average_true_range()

    rsi = df["rsi"].iloc[-1]
    macd_val = df["macd"].iloc[-1]
    macd_signal = df["macd_signal"].iloc[-1]
    ema_9 = df["ema_9"].iloc[-1]
    ema_21 = df["ema_21"].iloc[-1]
    ema_50 = df["ema_50"].iloc[-1]
    atr = df["atr"].iloc[-1]
    avg_price = df["close"].iloc[-10:].mean()

    confidence = 0
    direction = None

    if atr > avg_price * 0.005:  # Проверка на волатильность
        if rsi > 60:
            confidence += 20
            direction = "long"
        elif rsi < 40:
            confidence += 20
            direction = "short"

        if macd_val > macd_signal and direction == "long":
            confidence += 25
        elif macd_val < macd_signal and direction == "short":
            confidence += 25

        if ema_9 > ema_21 > ema_50 and direction == "long":
            confidence += 30
        elif ema_9 < ema_21 < ema_50 and direction == "short":
            confidence += 30

        if direction:
            confidence += min(25, (atr / avg_price) * 1000)

    if confidence >= config.CONFIDENCE_THRESHOLD:
        return direction, int(confidence)
    else:
        return None, int(confidence)

def send_signal(symbol, direction, confidence, price):
    msg = f"📈 Сигнал на {direction.upper()}\nПара: {symbol}\nЦена входа: {price}\nУверенность: {confidence}%"
    bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)

def main():
    last_report_time = time.time()

    while True:
        symbols = get_symbols()
        best = None
        best_conf = 0

        for symbol in symbols:
            df = get_klines(symbol)
            if df is None or df.empty:
                continue

            direction, confidence = analyze(df)
            print(f"[{symbol}] Направление: {direction}, Уверенность: {confidence}")

            if direction and confidence >= config.CONFIDENCE_THRESHOLD:
                current_price = df["close"].iloc[-1]
                send_signal(symbol, direction, confidence, current_price)

            if confidence > best_conf:
                best = (symbol, direction, confidence)
                best_conf = confidence

        if best:
            print(f"🔥 Лучшая пара: {best[0]} | {best[1]} | Уверенность: {best[2]}")

        if time.time() - last_report_time > 3600:
            bot.send_message(config.TELEGRAM_CHAT_ID, text="✅ Бот активен. Пока нет сигналов.")
            last_report_time = time.time()

        print("⏳ Ждём 5 минут...\n")
        time.sleep(300)

if __name__ == "__main__":
    main()
