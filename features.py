import pandas as pd
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import MFIIndicator

def prepare_features(df):
    if df is None or df.empty or len(df) < 100:
        return None, None

    df = df.copy()

    try:
        df['ema_fast'] = EMAIndicator(close=df['close'], window=10).ema_indicator()
        df['ema_slow'] = EMAIndicator(close=df['close'], window=30).ema_indicator()

        macd = MACD(close=df['close'])
        df['macd'] = macd.macd_diff()

        df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx()
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()

        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_bbm'] = bb.bollinger_mavg()
        df['bb_bbh'] = bb.bollinger_hband()
        df['bb_bbl'] = bb.bollinger_lband()

        df['mfi'] = MFIIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14).money_flow_index()

        # Целевая переменная: если следующая свеча закрылась выше текущей
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

        df = df.dropna()

        return df, df['target']

    except Exception as e:
        print(f"❌ Ошибка в prepare_features: {e}")
        return None, None
