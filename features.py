import pandas as pd
from ta.trend import MACD, CCIIndicator, ADXIndicator, EMAIndicator, TRIXIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volume import OnBalanceVolume

def prepare_features(df):
    df = df.copy()

    # Убедимся, что нет пропущенных значений
    df.dropna(inplace=True)

    # Простые индикаторы
    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    df['stoch_k'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch()
    df['stoch_d'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch_signal()
    df['macd'] = MACD(close=df['close']).macd()
    df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()
    df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
    df['ema'] = EMAIndicator(close=df['close']).ema_indicator()
    df['sma'] = SMAIndicator(close=df['close']).sma_indicator()
    df['trix'] = TRIXIndicator(close=df['close']).trix()
    df['obv'] = OnBalanceVolume(close=df['close'], volume=df['volume']).on_balance_volume()

    # Возвращаем только нужные колонки
    feature_columns = [
        'rsi', 'stoch_k', 'stoch_d', 'macd', 'cci', 'adx',
        'ema', 'sma', 'trix', 'obv'
    ]

    return df[feature_columns].dropna()
