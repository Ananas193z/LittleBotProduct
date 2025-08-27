from pybit.unified_trading import HTTP
from bybitchecker import get_price_from_bybit, get_aleivebel_balance
from trading_strategy import monitor_and_update_stop
from trading_utils import has_position
from telegram_send_logs import notify_async
from datetime import datetime, timedelta
import time
import re
import threading
from config import *



def start_traiding(session, signal_message, signal_data):
    print('Start trading')
    #balance = session.get_wallet_balance(accountType="UNIFIED")
    #balancebybit = get_aleivebel_balance(balance)
    balancebybit = 10000
    NOW_LEVERAGE = PLECHO
    
    trading_pair      = signal_data["symbol"]
    side              = signal_data["side"]

    entry_price       = float(signal_data["entry"])
    tp_profits        = []
    for i in signal_data["take_profits"]:
        tp_profits.append(float(i["price"]))

    tp_price          = tp_profits[3]
    if str(side) == 'Buy':
        sl_price = float(entry_price) * (1 - ((main_stoploss/NOW_LEVERAGE)/100))
    elif str(side) == 'Sell':
        sl_price = float(entry_price) * (((main_stoploss/NOW_LEVERAGE)/100) + 1)
    
    
    realprice = get_price_from_bybit(trading_pair)
    amountforstart = round((float(balancebybit) * (nowprcentforstart / 100)), 2)
    doladlastartafiltered = int(round((amountforstart/realprice), 0) * int(NOW_LEVERAGE))
    
    filter_resp = session.get_instruments_info(category="linear", symbol=trading_pair)
    filters = filter_resp["result"]["list"][0]["lotSizeFilter"]
    max_qty = float(filters["maxMktOrderQty"])
    
    if doladlastartafiltered > max_qty:
        doladlastartafiltered = max_qty
        amountforstart = round((doladlastartafiltered / NOW_LEVERAGE) * realprice, 2)

    
    
    order = {
        "category": "linear",
        "symbol": trading_pair,
        "side": side,                # "Buy" или "Sell"
        "orderType": "Market",       # ← МАРКЕТ

        "qty": str(doladlastartafiltered),  # ОБЯЗАТЕЛЬНО строкой

        "takeProfit": str(tp_price),
        "stopLoss": str(sl_price),
        "tpTriggerBy": "LastPrice",
        "slTriggerBy": "LastPrice",

        "tpslMode": "Full",          # На всю позицию
        "tpOrderType": "Market",     # По рынку
        "slOrderType": "Market",     # По рынку

        "positionIdx": 0,             # 0 = one-way (если не hedge)
        "reduceOnly": False,           # Открываем, а не закрываем
    }

    try:
        session.set_leverage(category="linear", symbol=trading_pair, buyLeverage=str(NOW_LEVERAGE), sellLeverage=str(NOW_LEVERAGE))
    except:
        print('Плечё уже установлено')
        
    entry_time = datetime.utcnow() - timedelta(seconds=1)
    
    try:
        resp = session.place_order(**order)
        start_order_id = resp["result"]["orderId"]
        print(start_order_id)
        notify_async(signal_message)
        time.sleep(0.05)
        notify_async(f'✅ Order created! ID: {start_order_id}\nBot entered with amount: {amountforstart}\nWith leverage: {NOW_LEVERAGE}\nAmount * Leverage: {round(float(amountforstart)*int(NOW_LEVERAGE), 2)}')
    except Exception as e:
        error_text = str(e)
        print("❌ Ошибка:", error_text)
        
        # Парсим плечо из текста ошибки
        match = re.search(r"adjust your leverage to (\d+)", error_text)
        if match:
            new_leverage = int(match.group(1))
            NOW_LEVERAGE = new_leverage
            print(f"🔁 Меняем плечо на {NOW_LEVERAGE} и пробуем снова...")

            doladlastartafiltered = int(round((amountforstart / realprice), 0) * NOW_LEVERAGE)
            
            if doladlastartafiltered > max_qty:
                doladlastartafiltered = max_qty
                amountforstart = round((doladlastartafiltered / NOW_LEVERAGE) * realprice, 2)
                
            if str(side) == 'Buy':
                sl_price = float(entry_price) * (1 - ((main_stoploss/NOW_LEVERAGE)/100))
            elif str(side) == 'Sell':
                sl_price = float(entry_price) * (((main_stoploss/NOW_LEVERAGE)/100) + 1)
            
            order["qty"] = str(doladlastartafiltered)
            order["stopLoss"] = str(sl_price)


            session.set_leverage(
                category="linear", symbol=trading_pair,
                buyLeverage=str(NOW_LEVERAGE), sellLeverage=str(NOW_LEVERAGE)
            )

            resp = session.place_order(**order)
            start_order_id = resp["result"]["orderId"]
            print(start_order_id)
            notify_async(signal_message)
            time.sleep(0.05)
            notify_async(f'✅ Order created with reduced leverage! ID: {start_order_id}\nBot entered with amount: {amountforstart}\nWith leverage: {NOW_LEVERAGE}\nAmount * Leverage: {round(float(amountforstart)*int(NOW_LEVERAGE), 2)}')
        else:
            print("⚠️ Не удалось распознать нужное плечо из ошибки.")
            return


        
    monitor_and_update_stop(session, trading_pair, side, doladlastartafiltered, tp_profits, prcents, stoploss_fist, start_order_id, entry_time, NOW_LEVERAGE)
