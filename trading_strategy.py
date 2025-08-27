# trading_utils.py
import time
from config import *
from trading_utils  import *
from datetime import datetime, timedelta
from telegram_send_logs import notify_async


def monitor_and_update_stop(session, symbol, action, total_size, tp_profits, prcents, stoploss_fist, market_order_id, entry_time, NOW_LEVERAGE):
    # Определяем закрывающую сторону: если позиция открыта на Buy (лонг), для закрытия используется Sell; если Sell — то Buy.
    start_ms = int(entry_time.timestamp() * 1000)
    ostatok = 0
    closing_side = "Sell" if action == "Buy" else "Buy"

    # Получаем данные ордера для получения цены входа (entry price)
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
    
    if entry_price is None:
        return

    # Рассчитываем параметры лимитного ордера
    first_qty = round((total_size * (prcents[0]/100)), 0)
    #first_take_profit = tp_profits[0]
    
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
        "side": closing_side,       # Используем переменную closing_side
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
    first_limit_order_id = first_limit_order_response["result"]["orderId"]
    
    
    
    
        
    second_qty = round((total_size * (prcents[1]/100)), 0)
    second_take_profit = tp_profits[1]
    print("Рассчитанная цена для лимитного ордера:", second_take_profit)

    # Размещаем лимитный ордер на закрытие 50% позиции с reduceOnly=True, используя closing_side
    second_order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": closing_side,       # Используем переменную closing_side
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
    second_limit_order_id = second_limit_order_response["result"]["orderId"]
    
    
    
    
        
    third_qty = round((total_size * (prcents[2]/100)), 0)
    third_take_profit = tp_profits[2]
    print("Рассчитанная цена для лимитного ордера:", third_take_profit)

    # Размещаем лимитный ордер на закрытие 50% позиции с reduceOnly=True, используя closing_side
    third_order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": closing_side,       # Используем переменную closing_side
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
    third_limit_order_id = third_limit_order_response["result"]["orderId"]
    
    
    
    
    
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
    # try:
    #     first_exit_time = datetime.utcnow()
    #     first_end_ms = int(first_exit_time.timestamp() * 1000)
    #     first_pnl = get_closed_pnl(session, symbol, start_ms, first_end_ms)
    #     for d in first_pnl:
    #         first_pnl_formated = f"[{d['symbol']}] Закрыт ордер {d['orderId']} | PNL: {d['closedPnl']} | Side: {d['side']} | Entry: {d['avgEntryPrice']} → Exit: {d['avgExitPrice']}"
    #     notify_async(first_pnl_formated)
    # except:
    #     print('First get pnl error')

    
    
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
    # try:
    #     second_exit_time = datetime.utcnow()
    #     second_end_ms = int(second_exit_time.timestamp() * 1000)
    #     second_pnl = get_closed_pnl(session, symbol, start_ms, second_end_ms)
    #     for d in second_pnl:
    #         second_pnl_formated = f"[{d['symbol']}] Закрыт ордер {d['orderId']} | PNL: {d['closedPnl']} | Side: {d['side']} | Entry: {d['avgEntryPrice']} → Exit: {d['avgExitPrice']}"
    #     notify_async(second_pnl_formated)
    # except:
    #     print('Second get pnl error')
    
    
    
    
    
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
    # try:
    #     third_exit_time = datetime.utcnow()
    #     third_end_ms = int(third_exit_time.timestamp() * 1000)
    #     third_pnl = get_closed_pnl(session, symbol, start_ms, third_end_ms)
    #     for d in third_pnl:
    #         third_pnl_formated = f"[{d['symbol']}] Закрыт ордер {d['orderId']} | PNL: {d['closedPnl']} | Side: {d['side']} | Entry: {d['avgEntryPrice']} → Exit: {d['avgExitPrice']}"
    #     notify_async(third_pnl_formated)
    # except:
    #     print('Third get pnl error')
    
    
    
    
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
    notify_async(f'{symbol} Стоп лосс перемещён на уровень: {newstoploss}')
    
    
    while True:
        _, size_cur, avg_price = current_position_bybit(session, symbol)
        print(size_cur)
        if size_cur == 0:
            notify_async(f'{symbol} Стоп лосс ❌ (+{stoploss_fist}%)')
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
