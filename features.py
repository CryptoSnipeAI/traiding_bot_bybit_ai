# features.py
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolume

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
    df["obv"] = OnBalanceVolume(close=df["close"], volume=df["volume"]).on_balance_volume()
    df = df.dropna()
    return df, None


