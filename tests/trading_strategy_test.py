import time
from core.config import FIRST_STOPLOSS, API_KEY, API_SECRET
from core.main_core.help_func.current_position_bybit import calculate_new_stoploss
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


if __name__ == '__main__':
    session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)
    symbol = 'VELODROMEUSDT'
    total_size = 45000
    action = 'Buy'
    NOW_LEVERAGE = 20
    market_order_id = ''
    
    # Take profit and quantities
    take_profits = [0.05663, 0.05724]          # Can add more if needed
    quantities = [31500, 9000, 4275]

    # Get entry price
    entry_price = get_entry_price(session, symbol, market_order_id)
    print("Entry price (BE):", entry_price)

    # Calculate first stop loss
    new_stop_loss = calculate_new_stoploss(entry_price, action, FIRST_STOPLOSS, NOW_LEVERAGE)

    # Define steps: each step is a dict with qty, tp, messages, stop price
    steps = [
        {
            "qty": quantities[0],
            "tp": take_profits[0],
            "tp_msg": f'{symbol} First take ✅ (+40%)',
            "sl_msg": f'{symbol} Stop loss ❌ (-20%)',
            "stop_price": new_stop_loss
        },
        {
            "qty": quantities[1],
            "tp": take_profits[1],
            "tp_msg": f'{symbol} Second take ✅ (+60%)',
            "sl_msg": f'{symbol} Stop loss ❌ (+{FIRST_STOPLOSS}%)',
            "stop_price": take_profits[0]
        },
        {
            "qty": quantities[2],
            "tp": None,  # No TP price needed, just final stop
            "tp_msg": f'{symbol} Third take ✅ (+80%)',
            "sl_msg": f'{symbol} Stop loss ❌ (+{take_profits[0]}%)',
            "stop_price": take_profits[1]
        }
    ]

    remaining_size = total_size
    for step in steps:
        target_size = max(0, remaining_size - step["qty"] * 0.99)
        remaining_size = wait_for_position_fill(
            session,
            symbol,
            target_size,
            step["tp_msg"],
            step["sl_msg"]
        )
        update_stop_loss(session, symbol, action, step["stop_price"])
