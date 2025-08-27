import time
from logs.telegram_send_logs import notify_async
from core.utils.trading_utils import current_position_bybit
from pybit.unified_trading import HTTP


def get_entry_price(session, symbol, order_id):
    """Get entry price (lastPriceOnCreated) by order."""
    pos_data = session.get_open_orders(category="linear", symbol=symbol, order_id=order_id)
    if "result" in pos_data and pos_data["result"]["list"]:
        try:
            return float(pos_data["result"]["list"][0]["lastPriceOnCreated"])
        except Exception as e:
            print("Error retrieving entry price:", e)
            return None
    print("Failed to get data for the open position.")
    return None


def wait_for_position_fill(session, symbol, target_size, tp_message, sl_message):
    """Wait until position size reaches target or zero, then notify."""
    while True:
        _, size_cur, _ = current_position_bybit(session, symbol)
        if size_cur == 0:
            notify_async(sl_message)
            return size_cur
        elif size_cur <= target_size:
            notify_async(tp_message)
            return size_cur
        time.sleep(1)


def update_stop_loss(session, symbol, side, stop_price):
    """Set new stop loss and notify."""
    resp = session.set_trading_stop(
        category="linear",
        symbol=symbol,
        side=side,
        stopLoss=stop_price,
        positionIdx=0
    )
    print("Stop loss updated:", resp)
    notify_async(f'{symbol} Stop loss moved to level: {stop_price}')
    return resp