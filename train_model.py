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

# Список топовых пар
TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
    "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT"
]

# Получение данных
def get_klines(symbol, interval="15", limit=500):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    if "result" not in data or "list" not in data["result"]:
        raise Exception(f"Ошибка при получении данных для {symbol}")
    df = pd.DataFrame(data["result"]["list"], columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df = df.astype(float)
    return df

# Обработка признаков
def prepare_features(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    df["stoch_rsi"] = StochRSIIndicator(close=df["close"]).stochrsi_k()
    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = df["macd"] - df["macd_signal"]
    df["atr"] = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"]).average_true_range()
    df["volatility"] = (df["high"] - df["low"]) / df["close"]
    df["price_change"] = df["close"].pct_change()
    df["ema20_close_ratio"] = df["close"] / df["ema20"]
    df["ema50_close_ratio"] = df["close"] / df["ema50"]
    df["volume_change"] = df["volume"].pct_change()
    df["return_5"] = df["close"].pct_change(periods=5)
    df = df.dropna()
    return df

# Создание целевой переменной
def prepare_target(df, low=0.01, high=0.03, forward=3):
    df["future_max"] = df["close"].shift(-forward).rolling(window=forward).max()
    df["return"] = (df["future_max"] - df["close"]) / df["close"]
    df["target"] = ((df["return"] >= low) & (df["return"] <= high)).astype(int)
    df = df.dropna()
    return df

# Обучение модели
all_X, all_y = [], []

for symbol in TOP_SYMBOLS:
    try:
        df = get_klines(symbol)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df = prepare_features(df)
        df = prepare_target(df)
        X = df[[
            "rsi", "stoch_rsi", "ema20", "ema50", "macd", "macd_signal", "macd_diff",
            "atr", "volatility", "price_change", "ema20_close_ratio",
            "ema50_close_ratio", "volume_change", "return_5", "volume"
        ]]
        y = df["target"]
        all_X.append(X)
        all_y.append(y)
        print(f"✅ {symbol} готов")
    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

# Объединение данных
X_all = pd.concat(all_X, ignore_index=True)
y_all = pd.concat(all_y, ignore_index=True)

# Инициализация и обучение модели
model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.08,
    use_label_encoder=False,
    eval_metric="logloss"
)
model.fit(X_all, y_all)

# Сохранение модели
joblib.dump(model, "model.pkl")
print("✅ Новая модель обучена и сохранена как model.pkl")
