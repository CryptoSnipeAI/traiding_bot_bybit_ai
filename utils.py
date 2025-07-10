import pandas as pd
import requests
import time

def fetch_klines(symbol, interval='15m', limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",  # Для фьючерсов
        "symbol": symbol,
        "interval": interval,  # <-- ОБЯЗАТЕЛЬНО с "m" (например '15m')
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(f"ℹ️ API ответ {symbol}: {data}")

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
        print(f"❌ Ошибка запроса {symbol}: {e}")
        time.sleep(1)
        return None
