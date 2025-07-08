# get_pairs.py
import requests

def get_top_pairs(min_volume_usdt=10000000):
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    res = requests.get(url)
    data = res.json()

    if not data.get("result") or not data["result"].get("list"):
        return []

    pairs = []
    for item in data["result"]["list"]:
        symbol = item["symbol"]
        volume = float(item["turnover24h"])
        if symbol.endswith("USDT") and "1000" not in symbol and volume >= min_volume_usdt:
            pairs.append(symbol)

    return pairs

if __name__ == "__main__":
    print(get_top_pairs())
