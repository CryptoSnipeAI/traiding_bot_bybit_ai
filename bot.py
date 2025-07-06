import time
import requests
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from telegram import Bot
import config
import traceback

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

def get_symbols():
    urls = [
        "https://api.bybit.com/v5/market/instruments?category=linear",  # основной
        "https://api.bybit.com/v2/public/symbols"  # fallback, старый API
    ]

    for url in urls:
        try:
            print(f"Пробуем получить пары: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # V5 API
            if "result" in data and "list" in data["result"]:
                instrument_list = data["result"]["list"]
                symbols = [item["symbol"] for item in instrument_list if item.get("symbol", "").endswith("USDT")]
                print(f"✅ Получено {len(symbols)} символов от V5 API")
                return symbols

            # Fallback: старый API
            elif "result" in data:
                instrument_list = data["result"]
                symbols = [item["name"] for item in instrument_list if item.get("quote_currency") == "USDT"]
                print(f"✅ Получено {len(symbols)} символов от старого API")
                return symbols

        except Exception as e:
            print(f"❌ Ошибка при получении пар с {url}: {e}")
            print("Ответ API:")
            print(response.text if 'response' in locals() else 'нет ответа')
            traceback.print_exc()
    
    return []

def get_klines(symbol):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=15&limit=100"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()["result"]["list"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
        df = df.astype({"close": float, "high": float, "low": float, "volume": float})
        return df
    except Exception as e:
        print(f"Ошибка при получении свечей для {symbol}: {e}")
        traceback.print_exc()
        return None

def analyze(df):
    try:
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

        if atr > avg_price * 0.005:
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

        return (direction, int(confidence)) if confidence >= config.CONFIDENCE_THRESHOLD else (None, int(confidence))
    except Exception as e:
        print(f"Ошибка в анализе данных: {e}")
        traceback.print_exc()
        return None, 0

def send_signal(symbol, direction, confidence, price):
    try:
        msg = f"📈 Сигнал на {direction.upper()}\nПара: {symbol}\nЦена входа: {price}\nУверенность: {confidence}%"
        print(f"📤 Отправка сигнала: {msg}")
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Ошибка при отправке сигнала: {e}")
        traceback.print_exc()

def main():
    last_report_time = time.time()
    print("✅ Бот запущен, начинаем работу.")

    try:
        bot.send_message(config.TELEGRAM_CHAT_ID, text="✅ Бот запущен и готов к анализу рынка.")
    except Exception as e:
        print(f"Ошибка при отправке приветствия: {e}")
        traceback.print_exc()

    while True:
        try:
            print("🔍 Получаем список торговых пар...")
            symbols = get_symbols()
            if not symbols:
                print("⚠️ Пар нет, спим 1 минуту...")
                time.sleep(60)
                continue

            best = None
            best_conf = 0

            for symbol in symbols:
                print(f"📊 Анализ: {symbol}")
                df = get_klines(symbol)
                if df is None or df.empty:
                    print(f"⛔️ Нет данных по {symbol}, пропускаем.")
                    continue

                direction, confidence = analyze(df)
                print(f"{symbol}: направление={direction}, уверенность={confidence}%")

                if direction and confidence >= config.CONFIDENCE_THRESHOLD:
                    price = df["close"].iloc[-1]
                    send_signal(symbol, direction, confidence, price)

                if confidence > best_conf:
                    best = (symbol, direction, confidence)
                    best_conf = confidence

            if best:
                print(f"🔥 Лучшая пара: {best[0]} | Направление: {best[1]} | Уверенность: {best[2]}%")

            if time.time() - last_report_time > 600:  # 10 минут
                bot.send_message(config.TELEGRAM_CHAT_ID, text="🤖 Бот активен, жду возможности войти в сделку.")
                last_report_time = time.time()

            print("⏳ Пауза 5 минут...\n")
            time.sleep(300)

        except Exception as e:
            print(f"❌ Ошибка в основном цикле: {e}")
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
