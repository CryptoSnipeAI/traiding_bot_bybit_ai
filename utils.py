import pandas as pd
import requests
import time

def fetch_klines(symbol, interval='15', limit=200):
    url = "https://api.bybit.com/v5/market/kline"

    params = {
        "category": "linear",  # Фьючерсы
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("retCode") != 0:
            print(f"❌ API ошибка {symbol}: {data.get('retMsg', 'Unknown')}")
            return None

        candles = data.get("result", {}).get("list", [])
        if not candles:
            print(f"❌ {symbol} ошибка: пустой список свечей")
            return None

        df = pd.DataFrame(candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])

        # Преобразуем типы данных
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
        df = df.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float,
            'turnover': float
        })

        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        return df

    except Exception as e:
        print(f"❌ Ошибка при получении данных {symbol}: {e}")
        time.sleep(1)
        return None
