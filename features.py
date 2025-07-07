import pandas as pd
import pandas_ta as ta

def prepare(df):
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['ma50'] = ta.sma(df['close'], length=50)
    df['ma200'] = ta.sma(df['close'], length=200)
    df['future_close'] = df['close'].shift(-3)
    df['target'] = (df['future_close'] > df['close'] * 1.005).astype(int)
    df = df.dropna()
    X = df[['rsi', 'atr', 'ma50', 'ma200']].copy()
    y = df['target'].copy()
    return X, y
