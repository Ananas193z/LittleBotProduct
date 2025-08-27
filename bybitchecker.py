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
            print(f"❌ Токен {symbol} не найден на Bybit.")
            return None
    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")
        return None



def get_aleivebel_balance(balance):
    listofcoinsfrombb = balance['result']['list'][0]['coin']

    for i in listofcoinsfrombb:
        if str(i['coin']) == 'USDT':
            if (float(i['totalPositionIM']) > 0) or (float(i['totalOrderIM']) > 0):
                poschitanybalance = float(i['equity']) - float(i['totalOrderIM']) - float(i['totalPositionIM']) - float(i['unrealisedPnl'])
                return poschitanybalance
            else:
                poschitanybalance = float(i['equity'])
                return poschitanybalance




def check_on_bybit(contract):

    # Получаем символ токена
    try:
        parsebybit = bybittokens[contract]
        parts = parsebybit.split("|")
        token_symbol = parts[0]
    except:
        token_symbol = False

    if token_symbol:
        trading_pair = token_symbol  # Удаляем все пробелы
        print(f"✅ Токен найден: {token_symbol}, проверяем на Bybit как {trading_pair}")
        print(f"✅ Пара {trading_pair} доступна на Bybit!")
        return True
    else:
        print(f"❌ Токен с контрактом {contract} не найден .")
        return False


