import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator, StochRSIIndicator
from ta.trend import MACD, CCIIndicator, ADXIndicator, EMAIndicator, TEMAIndicator, TRIXIndicator, SMAIndicator
from ta.volume import OnBalanceVolume, MFIIndicator
from ta.volatility import AverageTrueRange
from ta.volatility import BollingerBands
from ta.utils import dropna

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = dropna(df)

    # Базовые признаки
    df['close'] = df['close']

    # Momentum
    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['willr'] = (df['high'] - df['close']) / (df['high'] - df['low']) * -100
    df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()
    df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
    df['obv'] = OnBalanceVolume(close=df['close'], volume=df['volume']).on_balance_volume()
    df['roc'] = ROCIndicator(close=df['close']).roc()
    df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()

    # Trend indicators
    df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
    df['ema_21'] = EMAIndicator(close=df['close'], window=21).ema_indicator()
    df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
    df['ema_200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
    df['tema'] = TEMAIndicator(close=df['close']).tema()
    df['trix'] = TRIXIndicator(close=df['close']).trix()

    # Volume
    df['mfi'] = MFIIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).money_flow_index()

    # VWAP (приближённый, через среднюю цены с объёмом)
    df['vwap'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
    df['vwap'] = df['vwap'].rolling(window=14).mean()

    # SuperTrend Signal (простая логика: close выше ema21 = 1, иначе 0)
    df['supertrend_signal'] = (df['close'] > df['ema_21']).astype(int)

    # Удаляем строки с NaN после расчётов
    df.dropna(inplace=True)

    # Целевая переменная — будет ли рост на 1%
    df['target'] = (df['close'].shift(-1) > df['close'] * 1.01).astype(int)

    return df
