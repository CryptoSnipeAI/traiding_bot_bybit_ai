
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import warnings
warnings.filterwarnings("ignore")

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
    "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

def get_klines(symbol, interval="15", limit=500):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    if "result" not in data or "list" not in data["result"]:
        raise Exception(f"Failed to fetch {symbol}: {data}")
    df = pd.DataFrame(data["result"]["list"], columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df = df.astype(float)
    return df

def prepare_features(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
    df["volatility"] = (df["high"] - df["low"]) / df["close"]
    df = df.dropna()
    return df

def prepare_target(df, profit_threshold_low=0.01, profit_threshold_high=0.03, forward=3):
    df["future_max"] = df["close"].shift(-forward).rolling(window=forward).max()
    df["future_min"] = df["close"].shift(-forward).rolling(window=forward).min()
    df["return_up"] = (df["future_max"] - df["close"]) / df["close"]
    df["return_down"] = (df["close"] - df["future_min"]) / df["close"]

    # Классы:
    # 1 - цена поднимется на 1-3% за следующие 3 свечи (long сигнал)
    # 0 - цена упадет на 1-3% (short сигнал)
    # -1 - остальные случаи (без сигнала)
    conditions = [
        (df["return_up"] >= profit_threshold_low) & (df["return_up"] <= profit_threshold_high),
        (df["return_down"] >= profit_threshold_low) & (df["return_down"] <= profit_threshold_high)
    ]
    choices = [1, 0]
    df["target"] = np.select(conditions, choices, default=-1)

    df = df[df["target"] != -1]  # Убираем нейтральные метки
    df = df.dropna()
    return df

all_X, all_y = [], []

for symbol in TOP_SYMBOLS:
    try:
        df = get_klines(symbol)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df = prepare_features(df)
        df = prepare_target(df)
        X = df[["rsi", "ema20", "ema50", "volatility", "volume", "close"]]
        y = df["target"]
        all_X.append(X)
        all_y.append(y)
        print(f"✅ {symbol} готов")
    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

X_all = pd.concat(all_X, ignore_index=True)
y_all = pd.concat(all_y, ignore_index=True)

model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42
)

model.fit(X_all, y_all)

joblib.dump(model, "model.pkl")
print("✅ Модель обучена и сохранена как model.pkl")
