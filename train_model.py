import os
import requests
import pandas as pd
from features import prepare
from xgboost import XGBClassifier
import joblib
from time import sleep

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Получить все фьючерсные пары
def get_futures_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
    response = requests.get(url).json()
    symbols = [
        item["symbol"]
        for item in response["result"]["list"]
        if item["status"] == "Trading" and item["contractType"] == "LinearPerpetual"
    ]
    return symbols

# Загрузить свечи
def get_klines(symbol, interval="1h", limit=500):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url).json()
    raw = response["result"]["list"]
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype(float)
    return df

# Обучить и сохранить модель
def train_and_save(symbol):
    try:
        print(f"🟡 Обрабатываю {symbol}")
        df = get_klines(symbol)
        X, y = prepare(df)
        if len(X) < 10:
            print(f"⚠️ Пропущено (мало данных): {symbol}")
            return
        model = XGBClassifier(n_estimators=50, max_depth=3, use_label_encoder=False, eval_metric='logloss')
        model.fit(X, y)
        joblib.dump(model, f"{MODELS_DIR}/{symbol}_xgb.pkl")
        print(f"✅ Сохранено: {symbol}")
    except Exception as e:
        print(f"❌ Ошибка с {symbol}: {e}")

def main():
    symbols = get_futures_symbols()
    print(f"📊 Найдено пар: {len(symbols)}")
    for symbol in symbols:
        train_and_save(symbol)
        sleep(0.4)  # чтобы не словить бан

if __name__ == "__main__":
    main()
