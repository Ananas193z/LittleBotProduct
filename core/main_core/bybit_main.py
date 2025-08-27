from tests.bybitchecker import get_price_from_bybit
from strategy.trading_strategy import monitor_and_update_stop
from logs.telegram_send_logs import notify_async
from datetime import datetime, timedelta
import time
import re
from core.config import *


def calculate_sl_price(entry_price: float, side: str, stoploss: float, leverage: float) -> float:
    if str(side) == 'Buy':
        return float(entry_price) * (1 - ((stoploss / leverage) / 100))
    elif str(side) == 'Sell':
        return float(entry_price) * (((stoploss / leverage) / 100) + 1)
    else:
        raise ValueError(f"Unknown direction of the transaction: {side}")

def place_and_notify(session, order: dict, signal_message: str, amount: float, leverage: int | float):
    """
    Размещает ордер и отправляет уведомления.
    """
    resp = session.place_order(**order)
    order_id = resp["result"]["orderId"]

    print(order_id)

    notify_async(signal_message)
    time.sleep(0.05)

    notify_async(
        f'✅ Order created! ID: {order_id}\n'
        f'Bot entered with amount: {amount}\n'
        f'With leverage: {leverage}\n'
        f'Amount * Leverage: {round(float(amount) * float(leverage), 2)}'
    )

    return order_id


def start_traiding(session, signal_message, signal_data):
    print('Start trading')
    NOW_LEVERAGE = PLECHO
    trading_pair = signal_data["symbol"]
    side = signal_data["side"]

    entry_price = float(signal_data["entry"])
    tp_profits = []
    for i in signal_data["take_profits"]:
        tp_profits.append(float(i["price"]))

    tp_price = tp_profits[3]
    sl_price = calculate_sl_price(entry_price, side, MAIN_STOPLOSS, NOW_LEVERAGE)
    real_price = get_price_from_bybit(trading_pair)
    amount_for_start = round((float(BALANCE_BYBIT) * (NOW_PERCENT_FOR_START / 100)), 2)
    dollar_start_filtered = int(round((amount_for_start/real_price), 0) * int(NOW_LEVERAGE))
    
    filter_resp = session.get_instruments_info(category="linear", symbol=trading_pair)
    filters = filter_resp["result"]["list"][0]["lotSizeFilter"]
    max_qty = float(filters["maxMktOrderQty"])
    
    if dollar_start_filtered > max_qty:
        dollar_start_filtered = max_qty
        amount_for_start = round((dollar_start_filtered / NOW_LEVERAGE) * real_price, 2)

    order = {
        "category": "linear",
        "symbol": trading_pair,
        "side": side,                # "Buy" или "Sell"
        "orderType": "Market",       # ← МАРКЕТ

        "qty": str(dollar_start_filtered),  # ОБЯЗАТЕЛЬНО строкой

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
        print('Plecho already installed')
        
    entry_time = datetime.utcnow() - timedelta(seconds=1)
    
    try:
        start_order_id = place_and_notify(session, order, signal_message, amount_for_start, NOW_LEVERAGE)
    except Exception as e:
        error_text = str(e)
        print("❌ Error:", error_text)
        
        # Парсим плечо из текста ошибки
        match = re.search(r"Adjust your leverage to (\d+)", error_text)
        if match:
            new_leverage = int(match.group(1))
            NOW_LEVERAGE = new_leverage
            print(f"🔁 We change the leverage to {NOW_LEVERAGE} and try again...")

            dollar_start_filtered = int(round((amount_for_start / real_price), 0) * NOW_LEVERAGE)
            
            if dollar_start_filtered > max_qty:
                dollar_start_filtered = max_qty
                amount_for_start = round((dollar_start_filtered / NOW_LEVERAGE) * real_price, 2)
                
            sl_price = calculate_sl_price(entry_price, side, MAIN_STOPLOSS, NOW_LEVERAGE)
            
            order["qty"] = str(dollar_start_filtered)
            order["stopLoss"] = str(sl_price)

            session.set_leverage(
                category="linear", symbol=trading_pair,
                buyLeverage=str(NOW_LEVERAGE), sellLeverage=str(NOW_LEVERAGE)
            )

            start_order_id = place_and_notify(session, order, signal_message, amount_for_start, NOW_LEVERAGE)
        else:
            print("⚠️ Could not recognize the desired plecho from error.")
            return

    monitor_and_update_stop(session, trading_pair, side, dollar_start_filtered, tp_profits, PERCENTS, FIRST_STOPLOSS, start_order_id, entry_time, NOW_LEVERAGE)
