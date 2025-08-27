import requests


def get_price_from_bybit(symbol):
    """Получает текущую цену токена на Bybit (фьючерсы)"""
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear", "symbol": symbol}  # "linear" = USDT-фьючерсы

    try:
        response = requests.get(url, params=params).json()
        # Проверяем, есть ли данные
        if response["retCode"] == 0 and "list" in response["result"]:
            ticker_data = response["result"]["list"][0]  # Берем первый элемент (единственный)
            price = ticker_data["lastPrice"]  # Получаем цену
            return float(price)  # Конвертируем в число
        else:
            print(f"❌ The {symbol} token was not found on Bybit.")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None


