# features.py
from ta.momentum import RSIIndicator, StochRSIIndicator, AwesomeOscillatorIndicator
from ta.trend import EMAIndicator, MACD, CCIIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
import pandas as pd

def prepare_features(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    df["stoch_rsi"] = StochRSIIndicator(close=df["close"]).stochrsi_k()
    df["ao"] = AwesomeOscillatorIndicator(high=df["high"], low=df["low"]).awesome_oscillator()

    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()

    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    df["cci"] = CCIIndicator(high=df["high"], low=df["low"], close=df["close"], window=20).cci()
    df["adx"] = ADXIndicator(high=df["high"], low=df["low"], close=df["close"]).adx()

    bb = BollingerBands(close=df["close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]

    df["atr"] = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"]).average_true_range()

    df["volatility"] = (df["high"] - df["low"]) / df["close"]
    df["price_change"] = df["close"].pct_change()

    df = df.dropna()
    return df, None



