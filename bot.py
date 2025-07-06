import time
import traceback
import pandas as pd
from telegram import Bot
from pybit import usdt_perpetual
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import config

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
session = usdt_perpetual.HTTP("https://api.bybit.com")

def get_symbols():
    try:
        info = session.query_symbol()
        symbols = [s['name'] for s in info['result'] if s['quote_currency'] == 'USDT']
        print(f"✅ Получено {len(symbols)} пар через pybit")
        return symbols
    except Exception as e:
        print("❌ Ошибка get_symbols:", e)
        traceback.print_exc()
        return []

def get_klines(symbol):
    try:
        resp = session.query_kline(symbol=symbol, interval="15", limit=100)
        data = resp['result']
        df = pd.DataFrame(data)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        print(f"❌ Ошибка get_klines {symbol}:", e)
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
        msg = f"📈 Сигнал на {direction.upper()}
Пара: {symbol}
Цена входа: {price}
Уверенность: {confidence}%")
        print(f"Отправка сигнала: {msg}")
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Ошибка при отправке сигнала: {e}")
        traceback.print_exc()

def main():
    last_report_time = time.time()
    print("Бот запущен, начинаем работу.")
    try:
        bot.send_message(config.TELEGRAM_CHAT_ID, text="✅ Бот успешно запущен и готов к работе.")
    except Exception as e:
        print(f"Ошибка при отправке приветственного сообщения: {e}")
        traceback.print_exc()

    while True:
        try:
            symbols = get_symbols()
            if not symbols:
                time.sleep(60)
                continue

            best = None
            best_confidence = 0

            for symbol in symbols:
                df = get_klines(symbol)
                if df is None or df.empty:
                    continue
                direction, confidence = analyze(df)
                print(f"{symbol}: направление={direction}, уверенность={confidence}%")
                if direction and confidence >= config.CONFIDENCE_THRESHOLD:
                    price = df["close"].iloc[-1]
                    send_signal(symbol, direction, confidence, price)
                if confidence > best_confidence:
                    best = (symbol, direction, confidence)
                    best_confidence = confidence

            if best:
                print(f"🔥 Лучшая пара: {best[0]} | Направление: {best[1]} | Уверенность: {best[2]}%")

            if time.time() - last_report_time > 3600:
                bot.send_message(config.TELEGRAM_CHAT_ID, text="⌛ Бот работает.")
                last_report_time = time.time()

            time.sleep(300)
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
