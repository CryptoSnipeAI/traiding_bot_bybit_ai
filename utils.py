import pandas as pd
import requests
from datetime import datetime, timedelta

def fetch_klines(symbol, interval='15', limit=200):
    url = "https://api.bybit.com/v5/market/kline"

    # ⏱️ Устанавливаем `end` как текущее UTC время - 5 минут
    now = datetime.utcnow() - timedelta(minutes=5)
    end = int(now.timestamp() * 1000)

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "end": end
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(f"ℹ️ API ответ {symbol}: {data}")

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
        return df

    except Exception as e:
        print(f"❌ Ошибка запроса {symbol}: {e}")
        return None
