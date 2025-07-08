# features.py
import pandas as pd
import ta

def prepare(df: pd.DataFrame):
    df = df.copy()

    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd_diff()
    df['ema'] = ta.trend.EMAIndicator(df['close']).ema_indicator()
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_width'] = bb.bollinger_wband()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
    df['volatility'] = df['high'] - df['low']

    df = df.dropna()
    X = df[['rsi', 'macd', 'ema', 'bb_width', 'adx', 'volatility']]
    y = df['target'] if 'target' in df else None
    return X, y
