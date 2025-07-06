import requests, traceback

print("🔍 Начинаем тест API Bybit...")

for url in [
    "https://api.bybit.com/v5/market/instruments?category=linear",
    "https://api.bybit.com/v2/public/symbols"
]:
    try:
        r = requests.get(url, timeout=10)
        print(f"URL: {url} → статус {r.status_code}")
        print("Тело:", r.text[:200])
    except Exception as e:
        print(f"Ошибка при запросе {url}:", e)
        traceback.print_exc()