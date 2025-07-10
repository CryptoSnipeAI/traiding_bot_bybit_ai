import pandas as pd
import joblib
import os
from data_fetch import get_klines
from features import prepare_features

# Путь для сохранения модели
MODEL_PATH = "model.pkl"

# Список тикеров (можно изменить на top 20 или все доступные)
tickers = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT",
    "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT",
    "XLMUSDT", "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

all_X = []
all_y = []

for symbol in tickers:
    try:
        print(f"✅ Загружаю {symbol}")
        df = get_klines(symbol=symbol, interval="15m", limit=300)
        df = prepare_features(df)

        # Проверка: все признаки на месте
        expected_features = [
            'close', 'rsi', 'stoch_k', 'stoch_d', 'macd', 'macd_signal',
            'willr', 'cci', 'adx', 'obv', 'roc', 'atr', 'ema_9', 'ema_21',
            'ema_50', 'ema_200', 'tema', 'trix', 'mfi', 'vwap', 'supertrend_signal'
        ]

        # Пропускаем, если есть пропуски или недостающие признаки
        if df[expected_features].isnull().any().any():
            print(f"⚠️ Пропускаем {symbol}: есть пропущенные значения")
            continue

        X = df[expected_features]
        y = df["target"]  # Целевая переменная

        all_X.append(X)
        all_y.append(y)

        print(f"✅ {symbol} готов")

    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

# Объединяем все данные
if not all_X or not all_y:
    raise ValueError("Нет данных для обучения. Все тикеры не прошли фильтр.")

X_all = pd.concat(all_X, ignore_index=True)
y_all = pd.concat(all_y, ignore_index=True)

print("📊 Объём данных:", X_all.shape)

# Обучаем модель
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_all, y_all)

# Сохраняем модель
joblib.dump(model, MODEL_PATH)
print(f"✅ Модель обучена и сохранена как {MODEL_PATH}")
