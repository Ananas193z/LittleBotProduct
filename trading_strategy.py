from trading_utils  import *
from telegram_send_logs import notify_async


def monitor_and_update_stop(session, symbol, action, total_size, tp_profits, prcents, stoploss_fist, market_order_id, entry_time, NOW_LEVERAGE):
    closing_side = "Sell" if action == "Buy" else "Buy"

    def get_entry_price(session, symbol, order_id):
        """Получает цену входа (lastPriceOnCreated) по ордеру."""
        pos_data = session.get_open_orders(category="linear", symbol=symbol, order_id=order_id)
        if "result" in pos_data:
            try:
                return float(pos_data["result"]["list"][0]["lastPriceOnCreated"])
            except Exception as e:
                print("Ошибка при извлечении цены входа:", e)
                return None
        else:
            print("Не удалось получить данные открытой позиции.")
            return None

    # Получаем данные ордера для получения цены входа (entry price)
    entry_price = get_entry_price(session, symbol, market_order_id)
    print("Цена входа (БЕ):", entry_price)

    # Рассчитываем параметры лимитного ордера
    first_qty = round((total_size * (prcents[0]/100)), 0)
    
    if str(action) == 'Buy':
        first_take_profit = float(tp_profits[0]) * (1 - ((new_take_profit/NOW_LEVERAGE)/100))
    elif str(action) == 'Sell':
        first_take_profit = float(tp_profits[0]) * (((new_take_profit/NOW_LEVERAGE)/100) + 1)
    else:
        first_take_profit = tp_profits[0]
        
    print("Рассчитанная цена для лимитного ордера:", first_take_profit)
    notify_async(f'{symbol}\nEntry price: {entry_price}\nNew take profit: {first_take_profit}')

    # Размещаем лимитный ордер на закрытие 50% позиции с reduceOnly=True, используя closing_side
    first_order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": closing_side,
        "orderType": "Limit",
        "qty": first_qty,
        "price": first_take_profit,
        "timeInForce": "GTC",
        "reduceOnly": True,
        "positionIdx": 0
    }

    print(f"Размещаем лимитный ордер на закрытие {prcents[0]}% позиции по цене:", first_take_profit)
    first_limit_order_response = session.place_order(**first_order_data)
    print("Ответ от сервера:", first_limit_order_response)
    second_qty = round((total_size * (prcents[1]/100)), 0)
    second_take_profit = tp_profits[1]
    print("Рассчитанная цена для лимитного ордера:", second_take_profit)

    # Размещаем лимитный ордер на закрытие 50% позиции с reduceOnly=True, используя closing_side
    second_order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": closing_side,
        "orderType": "Limit",
        "qty": second_qty,
        "price": second_take_profit,
        "timeInForce": "GTC",
        "reduceOnly": True,
        "positionIdx": 0
    }

    print(f"Размещаем лимитный ордер на закрытие {prcents[1]}% позиции по цене:", second_take_profit)
    second_limit_order_response = session.place_order(**second_order_data)
    print("Ответ от сервера:", second_limit_order_response)
    third_qty = round((total_size * (prcents[2]/100)), 0)
    third_take_profit = tp_profits[2]
    print("Рассчитанная цена для лимитного ордера:", third_take_profit)

    # Размещаем лимитный ордер на закрытие 50% позиции с reduceOnly=True, используя closing_side
    third_order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": closing_side,
        "orderType": "Limit",
        "qty": third_qty,
        "price": third_take_profit,
        "timeInForce": "GTC",
        "reduceOnly": True,
        "positionIdx": 0
    }

    print(f"Размещаем лимитный ордер на закрытие {prcents[2]}% позиции по цене:", second_take_profit)
    third_limit_order_response = session.place_order(**third_order_data)
    print("Ответ от сервера:", third_limit_order_response)

    # Опрос статуса ордера каждую секунду
    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        if size_cur == 0:
            notify_async(f'{symbol} Stop loss 🛑 (-{main_stoploss}%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, total_size - first_qty * 0.99):
            notify_async(f'{symbol} First take profit 🟢 (+40%)')
            ostatok = size_cur
            break
        time.sleep(1)

    if str(action) == 'Buy':
        newstoploss = float(entry_price) * (((stoploss_fist/NOW_LEVERAGE)/100) + 1)
    elif str(action) == 'Sell':
        newstoploss = float(entry_price) * (1 - ((stoploss_fist/NOW_LEVERAGE)/100))
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
    notify_async(f'{symbol} 🛑 Stop loss moved to level: {newstoploss}')

    # Опрос статуса ордера каждую секунду
    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        if size_cur == 0:
            notify_async(f'{symbol} Stop loss 🛑 (+{stoploss_fist}%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, ostatok - second_qty * 0.99):
            notify_async(f'{symbol} Second take profit 🟢 (+60%)')
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
    notify_async(f'{symbol} 🛑 Stop loss moved to level: {first_take_profit}')

    # Опрос статуса ордера каждую секунду
    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        if size_cur == 0:
            notify_async(f'{symbol} Stop loss 🛑 (+38%)')
            ostatok = size_cur
            break
        elif size_cur <= max(0, ostatok - third_qty * 0.99):
            notify_async(f'{symbol} Third take profit 🟢 (+80%)')
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
    notify_async(f'{symbol} 🛑 Stop loss moved to level: {second_take_profit}')
