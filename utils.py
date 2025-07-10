import pandas as pd
import requests
import time

def fetch_klines(symbol, interval='15', limit=200):
    url = "https://api.bybit.com/v5/market/kline"

    params = {
        "category": "linear",  # это важно — именно для фьючерсов!
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("retCode") != 0 or "result" not in data or "list" not in data["result"]:
            print(f"❌ Ошибка API: {data.get('retMsg', 'Unknown')} для {symbol}")
            return None

        rows = data["result"]["list"]
        if not rows:
            return None

        df = pd.DataFrame(rows, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'turnover', 'confirm', 'cross_seq', 'timestamp_eof'
        ])

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df = df.astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
        return df

    except Exception as e:
        print(f"❌ Ошибка запроса {symbol}: {e}")
        time.sleep(1)
        return None
