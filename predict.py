import pickle
import pandas as pd
from features import prepare_features
from utils import fetch_klines

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
    "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

# Загружаем модель
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

signals = []

for symbol in symbols:
    print(f"📊 Обрабатываю {symbol}")
    try:
        df = fetch_klines(symbol, interval='15m', limit=100)

        if df is None or df.empty:
            print(f"❌ {symbol}: пустой DataFrame")
            continue

        features = prepare_features(df)
        if features is None or features.empty:
            print(f"❌ {symbol}: недопустимые признаки")
            continue

        X = features.drop(columns=['target'])
        prediction = model.predict(X.iloc[-1:].values)[0]
        confidence = model.predict_proba(X.iloc[-1:].values)[0][prediction]

        if prediction == 1 and confidence > 0.85:
            signals.append((symbol, confidence))
            print(f"✅ Сигнал LONG по {symbol} (уверенность: {confidence:.2f})")
        else:
            print(f"ℹ️ Нет сигнала по {symbol} (уверенность: {confidence:.2f})")

    except Exception as e:
        print(f"❌ Ошибка {symbol}: {e}")

if signals:
    print("\n🎯 Подходящие сигналы:")
    for s in signals:
        print(f"✅ {s[0]} — уверенность {s[1]:.2f}")
else:
    print("🚫 Подходящих сигналов не найдено.")
