import requests
import pandas as pd

def get_klines(symbol, interval='15', limit=1000):
    url = "https://api.bybit.com/v5/market/kline"
    resp = requests.get(url, params={
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }).json()
    df = pd.DataFrame(resp['result']['list'], columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ]).astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def get_all_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info"
    resp = requests.get(url, params={"category": "linear"}).json()
    return [item["symbol"] for item in resp["result"]["list"] if item["status"] == "Trading"]