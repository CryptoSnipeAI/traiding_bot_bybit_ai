import os
import requests
import pandas as pd
from features import prepare
from xgboost import XGBClassifier
import joblib
from time import sleep

# Получить список всех фьючерсных пар
def get_futures_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
    response = requests.get(url).json()
    symbols = [
        item["symbol"]
        for item in response["result"]["list"]
        if item["status"] == "Trading" and item["contractType"] == "LinearPerpetual"
    ]
    return symbols

# Получить OHLCV (свечи)
def get_klines(symbol, interval="1h", limit=500):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url).json()
    raw = response["result"]["list"]
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype(float)
    df["close"] = df["close"].astype(float)
    return df

# Обучить модель и сохранить в файл
def train_and_save(symbol):
    try:
        print(f"🟡 Обрабатываю: {symbol}")
        df = get_klines(symbol)
        X, y = prepare(df)

        if len(X) < 10:
            print(f"⚠️ Недостаточно данных: {symbol}")
            return

        model = XGBClassifier(
            n_estimators=50,
            max_depth=3,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        model.fit(X, y)

        filename = f"{symbol}_xgb.pkl"
        joblib.dump(model, filename)
        print(f"✅ Сохранена модель: {filename}")

    except Exception as e:
        print(f"❌ Ошибка при обработке {symbol}: {e}")

def main():
    symbols = get_futures_symbols()
    print(f"📊 Найдено {len(symbols)} фьючерсных пар")

    for symbol in symbols:
        train_and_save(symbol)
        sleep(0.4)  # пауза между запросами, чтобы не получить бан

if __name__ == "__main__":
    main()
