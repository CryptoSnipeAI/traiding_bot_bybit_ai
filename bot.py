import time
import requests
import pandas as pd
from telegram import Bot
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import config
import traceback

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

BASE_URL = "https://api.bybit.com"  # Основной API Bybit

def get_symbols():
    """
    Получаем список символов USDT спотов (линейных)
    """
    try:
        url = f"{BASE_URL}/v5/market/instruments?category=linear"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Проверяем структуру и фильтруем USDT пары
        if "result" in data and "list" in data["result"]:
            symbols = [item["symbol"] for item in data["result"]["list"] if item["symbol"].endswith("USDT")]
            print(f"✅ Получено {len(symbols)} торговых пар для анализа")
            return symbols
        else:
            print("❌ Нет списка торговых пар в ответе API")
            return []

    except Exception as e:
        print(f"❌ Ошибка при получении символов: {e}")
        traceback.print_exc()
        return []

def get_klines(symbol):
    """
    Получаем свечи 15 минут по символу
    """
    try:
        url = f"{BASE_URL}/v5/market/kline?category=linear&symbol={symbol}&interval=15&limit=100"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "list" in data["result"]:
            klines = data["result"]["list"]
            df = pd.DataFrame(klines, columns=["timestamp","open","high","low","close","volume","_","_","_","_","_","_"])
            for col in ["open","high","low","close","volume"]:
                df[col] = df[col].astype(float)
            return df
        else:
            print(f"❌ Нет данных по свечам для {symbol}")
            return None

    except Exception as e:
        print(f"❌ Ошибка при получении свечей {symbol}: {e}")
        traceback.print_exc()
        return None

def analyze(df):
    """
    Анализируем технические индикаторы и считаем уверенность сигнала
    """
    try:
        df["rsi"] = RSIIndicator(df["close"]).rsi()
        macd = MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["ema_9"] = EMAIndicator(df["close"], window=9).ema_indicator()
        df["ema_21"] = EMAIndicator(df["close"], window=21).ema_indicator()
        df["ema_50"] = EMAIndicator(df["close"], window=50).ema_indicator()
        df["atr"] = AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range()

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

        # Проверяем ATR - волатильность
        if atr > avg_price * 0.005:
            # RSI - покупка или продажа
            if rsi > 60:
                confidence += 20
                direction = "long"
            elif rsi < 40:
                confidence += 20
                direction = "short"

            # MACD подтверждение
            if macd_val > macd_signal and direction == "long":
                confidence += 25
            elif macd_val < macd_signal and direction == "short":
                confidence += 25

            # EMA тренд
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

    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        traceback.print_exc()
        return None, 0

def send_signal(symbol, direction, confidence, price):
    try:
        msg = (
            f"📈 Сигнал: {direction.upper()}\n"
            f"Пара: {symbol}\n"
            f"Цена входа: {price:.6f}\n"
            f"Уверенность: {confidence}%"
        )
        print(f"🔔 Отправка сигнала: {msg}")
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"❌ Ошибка отправки сигнала: {e}")
        traceback.print_exc()

def main():
    print("🚀 Бот запущен")
    try:
        bot.send_message(config.TELEGRAM_CHAT_ID, "✅ Бот запущен и готов к работе")
    except Exception as e:
        print(f"❌ Ошибка приветственного сообщения: {e}")

    last_ping = time.time()

    while True:
        try:
            symbols = get_symbols()
            if not symbols:
                print("⚠️ Нет пар, ждем минуту")
                time.sleep(60)
                continue

            best_confidence = 0
            best_signal = None

            for symbol in symbols:
                df = get_klines(symbol)
                if df is None or df.empty:
                    continue

                direction, confidence = analyze(df)
                print(f"{symbol}: {direction}, уверенность {confidence}%")

                if direction:
                    price = df["close"].iloc[-1]
                    send_signal(symbol, direction, confidence, price)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_signal = (symbol, direction, confidence)

            if best_signal:
                print(f"🔥 Лучший сигнал: {best_signal[0]} {best_signal[1]} {best_signal[2]}%")

            if time.time() - last_ping > 3600:
                bot.send_message(config.TELEGRAM_CHAT_ID, "⌛️ Бот жив и работает")
                last_ping = time.time()

            print("⏳ Ждем 5 минут")
            time.sleep(300)

        except Exception as e:
            print(f"❌ Ошибка в основном цикле: {e}")
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
