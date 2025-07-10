import pandas as pd
import requests
import time

def fetch_klines(symbol, interval='15m', limit=200):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("retCode") != 0 or "result" not in data or "list" not in data["result"]:
            print(f"❌ Ошибка API для {symbol}")
            return None

        rows = data["result"]["list"]
        df = pd.DataFrame(rows, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', '_', '__'
        ])

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
        return df

    except Exception as e:
        print(f"❌ Ошибка загрузки {symbol}: {e}")
        time.sleep(1)
        return None
