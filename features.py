import pandas as pd
from ta.trend import MACD, CCIIndicator, ADXIndicator, EMAIndicator, TRIXIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator

def calculate_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i - 1]:
            obv.append(obv[-1] + df['volume'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
            obv.append(obv[-1] - df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def prepare_features(df):
    df = df.copy()
    df.dropna(inplace=True)

    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    df['stoch_k'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch()
    df['stoch_d'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch_signal()
    df['macd'] = MACD(close=df['close']).macd()
    df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()
    df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
    df['ema'] = EMAIndicator(close=df['close']).ema_indicator()
    df['sma'] = SMAIndicator(close=df['close']).sma_indicator()
    df['trix'] = TRIXIndicator(close=df['close']).trix()
    df['obv'] = calculate_obv(df)

    return df[['rsi', 'stoch_k', 'stoch_d', 'macd', 'cci', 'adx', 'ema', 'sma', 'trix', 'obv']].dropna()
