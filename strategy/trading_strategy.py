import time
from core.main_core.help_func.current_position_bybit import calculate_new_stoploss, current_position_bybit
from logs.telegram_send_logs import notify_async
from core.config import MAIN_STOPLOSS, NEW_TAKE_PROFIT


def get_entry_price(session, symbol, order_id):
    """Get entry price (lastPriceOnCreated) by order."""
    pos_data = session.get_open_orders(category="linear", symbol=symbol, order_id=order_id)
    if "result" in pos_data:
        try:
            return float(pos_data["result"]["list"][0]["lastPriceOnCreated"])
        except Exception as e:
            print("Error while extracting entry price:", e)
            return None
    else:
        print("Could not get open position data.")
        return None


def place_limit_order(session, symbol, side, qty, price, percent):
    """Place a limit order and print logs."""
    order_data = {
        "category": "linear",
        "symbol": symbol,
        "side": side,
        "orderType": "Limit",
        "qty": qty,
        "price": price,
        "timeInForce": "GTC",
        "reduceOnly": True,
        "positionIdx": 0
    }
    print(f"Placing limit order to close {percent}% of position at price: {price}")
    resp = session.place_order(**order_data)
    print("Server response:", resp)
    return resp


def wait_for_fill(session, symbol, target_size, tp_message, sl_message):
    """Wait until the position is reduced or closed by stop loss."""
    while True:
        _, size_cur, _ = current_position_bybit(session, symbol)
        if size_cur == 0:
            notify_async(sl_message)
            return size_cur
        elif size_cur <= target_size:
            notify_async(tp_message)
            return size_cur
        time.sleep(1)


def monitor_and_update_stop(session, symbol, action, total_size, tp_profits, prcents, stoploss_fist, market_order_id, entry_time, NOW_LEVERAGE):
    closing_side = "Sell" if action == "Buy" else "Buy"

    # get entry price
    entry_price = get_entry_price(session, symbol, market_order_id)
    print("Entry price (BE):", entry_price)

    # calculate adjusted take profit for the first order
    if str(action) == 'Buy':
        tp_adjusted = float(tp_profits[0]) * (1 - ((NEW_TAKE_PROFIT / NOW_LEVERAGE) / 100))
    elif str(action) == 'Sell':
        tp_adjusted = float(tp_profits[0]) * (((NEW_TAKE_PROFIT / NOW_LEVERAGE) / 100) + 1)
    else:
        tp_adjusted = tp_profits[0]

    notify_async(f'{symbol}\nEntry price: {entry_price}\nNew take profit: {tp_adjusted}')

    # --- place take profits in a loop ---
    quantities = [round(total_size * (p / 100), 0) for p in prcents]
    take_profits = [tp_adjusted] + tp_profits[1:]

    ostatok = total_size
    for i, (qty, tp) in enumerate(zip(quantities, take_profits), start=1):
        place_limit_order(session, symbol, closing_side, qty, tp, prcents[i-1])
        print("Calculated price for limit order:", tp)

        # wait until order is filled
        if i == 1:
            ostatok = wait_for_fill(session, symbol, total_size - qty * 0.99,
                                    f'{symbol} First take profit 🟢 (+40%)',
                                    f'{symbol} Stop loss 🛑 (-{MAIN_STOPLOSS}%)')
            # move stop loss
            new_sl = calculate_new_stoploss(entry_price, action, stoploss_fist, NOW_LEVERAGE)
            resp = session.set_trading_stop(category="linear", symbol=symbol, side=action, stopLoss=new_sl, positionIdx=0)
            print("Stop loss updated:", resp)
            notify_async(f'{symbol} 🛑 Stop loss moved to level: {new_sl}')
        elif i == 2:
            ostatok = wait_for_fill(session, symbol, ostatok - qty * 0.99,
                                    f'{symbol} Second take profit 🟢 (+60%)',
                                    f'{symbol} Stop loss 🛑 (+{stoploss_fist}%)')
            resp = session.set_trading_stop(category="linear", symbol=symbol, side=action, stopLoss=take_profits[0], positionIdx=0)
            print("Stop loss updated:", resp)
            notify_async(f'{symbol} 🛑 Stop loss moved to level: {take_profits[0]}')
        elif i == 3:
            ostatok = wait_for_fill(session, symbol, ostatok - qty * 0.99,
                                    f'{symbol} Third take profit 🟢 (+80%)',
                                    f'{symbol} Stop loss 🛑 (+38%)')
            resp = session.set_trading_stop(category="linear", symbol=symbol, side=action, stopLoss=take_profits[1], positionIdx=0)
            print("Stop loss updated:", resp)
            notify_async(f'{symbol} 🛑 Stop loss moved to level: {take_profits[1]}')
