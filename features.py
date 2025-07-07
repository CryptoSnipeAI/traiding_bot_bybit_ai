import pandas as pd
import talib as ta

def prepare(df):
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)
    df['atr'] = ta.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['ma50'] = ta.SMA(df['close'], timeperiod=50)
    df['ma200'] = ta.SMA(df['close'], timeperiod=200)
    df['future_close'] = df['close'].shift(-3)
    df['target'] = (df['future_close'] > df['close'] * 1.005).astype(int)
    df = df.dropna()
    X = df[['rsi','atr','ma50','ma200']].copy()
    y = df['target'].copy()
    return X, y