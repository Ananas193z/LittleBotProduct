from datetime import time

from core.config import FIRST_STOPLOSS, API_KEY, API_SECRET
from logs.telegram_send_logs import notify_async
from core.utils.trading_utils import current_position_bybit
from pybit.unified_trading import HTTP

if __name__ == '__main__':
    session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)
    symbol = 'VELODROMEUSDT'
    total_size = 45000
    action = 'Buy'
    NOW_LEVERAGE = 20
    market_order_id = ''
    first_take_profit = 0.05663
    second_take_profit = 0.05724
    first_qty = 31500
    second_qty = 9000
    third_qty = 4275

    pos_data = session.get_open_orders(category="linear", symbol=symbol, order_id=market_order_id)
    if "result" in pos_data:
        try:
            entry_price = float(pos_data["result"]["list"][0]["lastPriceOnCreated"])
        except Exception as e:
            print("Ошибка при извлечении цены входа:", e)
            entry_price = None
        print("Цена входа (БЕ):", entry_price)
    else:
        print("Не удалось получить данные открытой позиции.")
        entry_price = None

    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        #print(size_cur)
        if size_cur == 0:
            notify_async(f'{symbol} Стоп лосс ❌ (-20%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, total_size - first_qty * 0.99):
            notify_async(f'{symbol} Перый тейк ✅ (+40%)')
            ostatok = size_cur
            break
        time.sleep(1)

    if str(action) == 'Buy':
        newstoploss = float(entry_price) * (((FIRST_STOPLOSS / NOW_LEVERAGE) / 100) + 1)
    elif str(action) == 'Sell':
        newstoploss = float(entry_price) * (1 - ((FIRST_STOPLOSS / NOW_LEVERAGE) / 100))
    else:
        newstoploss = float(entry_price)

    first_stop_resp = session.set_trading_stop(
        category="linear",
        symbol=symbol,
        side=action,
        stopLoss=newstoploss,
        positionIdx=0
    )
    print("Стоп-лосс обновлён:", first_stop_resp)
    notify_async(f'{symbol} Стоп лосс перемещён на уровень: {newstoploss}')

    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        print(size_cur)
        if size_cur == 0:
            notify_async(f'{symbol} Стоп лосс ❌ (+{FIRST_STOPLOSS}%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, ostatok - second_qty * 0.99):
            notify_async(f'{symbol} Второй тейк ✅ (+60%)')
            ostatok = size_cur
            break
        time.sleep(1)

    second_stop_resp = session.set_trading_stop(
        category="linear",
        symbol=symbol,
        side=action,
        stopLoss=first_take_profit,
        positionIdx=0
    )
    print("Стоп-лосс обновлён:", second_stop_resp)
    notify_async(f'{symbol} Стоп лосс перемещён на уровень: {newstoploss}')


    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        print(size_cur)
        if size_cur == 0:
            notify_async(f'{symbol} Стоп лосс ❌ (+{first_take_profit}%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, ostatok - third_qty * 0.99):
            notify_async(f'{symbol} Третий тейк ✅ (+80%)')
            ostatok = size_cur
            break
        time.sleep(1)

    third_stop_resp = session.set_trading_stop(
        category="linear",
        symbol=symbol,
        side=action,
        stopLoss=second_take_profit,
        positionIdx=0
    )
    print("Стоп-лосс обновлён:", third_stop_resp)
    notify_async(f'{symbol} Стоп лосс перемещён на уровень: {newstoploss}')