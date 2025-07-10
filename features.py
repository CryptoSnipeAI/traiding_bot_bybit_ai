# features.py
import pandas as pd
import numpy as np
from ta.trend import MACD, CCIIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    df['stoch_k'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch()
    df['stoch_d'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch_signal()
    df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()

    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'])
    df['adx'] = adx.adx()
    df['adx_pos'] = adx.adx_pos()
    df['adx_neg'] = adx.adx_neg()

    boll = BollingerBands(close=df['close'])
    df['bollinger_mavg'] = boll.bollinger_mavg()
    df['bollinger_hband'] = boll.bollinger_hband()
    df['bollinger_lband'] = boll.bollinger_lband()

    df['close_diff'] = df['close'].diff()
    df['close_pct'] = df['close'].pct_change()
    df['volume_diff'] = df['volume'].diff()
    df['volume_pct'] = df['volume'].pct_change()

    df = df.dropna()
    return df[[
        'rsi', 'stoch_k', 'stoch_d', 'cci', 'macd', 'macd_signal', 'macd_diff',
        'adx', 'adx_pos', 'adx_neg', 'bollinger_mavg', 'bollinger_hband', 'bollinger_lband',
        'close_diff', 'close_pct', 'volume_diff', 'volume_pct',
        'open', 'high', 'low', 'close'
    ]]


