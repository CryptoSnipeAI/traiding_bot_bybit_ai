import os
import pickle
import pandas as pd
from features import prepare_features
from utils import fetch_klines
from sklearn.ensemble import RandomForestClassifier

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
    "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

data = []

for symbol in symbols:
    print(f"✅ Загружаю {symbol}")
    try:
        df = fetch_klines(symbol, interval='15m', limit=1500)

        if df is None or df.empty:
            print(f"❌ {symbol} ошибка: пустой DataFrame")
            continue

        features = prepare_features(df)

        if features is None or features.empty or len(features) < 100:
            print(f"❌ {symbol} ошибка: недостаточно данных после обработки")
            continue

        data.append(features)

    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

if not data:
    raise ValueError("Нет данных для обучения. Все тикеры не прошли фильтр.")

df_all = pd.concat(data)

X = df_all.drop(columns=['target'])
y = df_all['target']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Модель обучена и сохранена как model.pkl")
