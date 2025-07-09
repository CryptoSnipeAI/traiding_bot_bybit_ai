
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import requests
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
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
    df["stoch_rsi"] = StochRSIIndicator(close=df["close"]).stochrsi_k()
    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["atr"] = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"]).average_true_range()
    df["volatility"] = (df["high"] - df["low"]) / df["close"]
    df = df.dropna()
    return df

def prepare_target(df, profit_threshold_low=0.01, profit_threshold_high=0.03, forward=3):
    df["future_max"] = df["close"].shift(-forward).rolling(forward).max()
    df["future_min"] = df["close"].shift(-forward).rolling(forward).min()
    df["return_max"] = (df["future_max"] - df["close"]) / df["close"]
    df["return_min"] = (df["future_min"] - df["close"]) / df["close"]

    # Класс 1 = LONG, класс 2 = SHORT, класс 0 = нейтральный
    df["target"] = 0
    df.loc[df["return_max"] >= profit_threshold_low, "target"] = 1
    df.loc[df["return_min"] <= -profit_threshold_low, "target"] = 2

    df = df.dropna()
    return df

all_X, all_y = [], []

for symbol in TOP_SYMBOLS:
    try:
        df = get_klines(symbol)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df = prepare_features(df)
        df = prepare_target(df)
        X = df[["rsi", "stoch_rsi", "ema20", "ema50", "macd", "macd_signal", "atr", "volatility", "volume", "close"]]
        y = df["target"]
        all_X.append(X)
        all_y.append(y)
        print(f"✅ {symbol} готов")
    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

X_all = pd.concat(all_X, ignore_index=True)
y_all = pd.concat(all_y, ignore_index=True)

model = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, use_label_encoder=False, eval_metric="mlogloss")
model.fit(X_all, y_all)

joblib.dump(model, "model.pkl")
print("✅ Модель обучена и сохранена как model.pkl")

