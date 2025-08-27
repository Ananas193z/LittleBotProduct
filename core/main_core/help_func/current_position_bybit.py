from core.config import *
from pybit.unified_trading import HTTP
import time
from logs.telegram_send_logs import sendMessageToTelegram
from tests.bybittest import entry_price, stoploss_fist

session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)

initial_qty = 11736.0
tp_qty = 0.4798
action = 'Buy'
closing_side = 'Sell'

def calculate_new_stoploss(entry_price: float, action: str, stoploss_percent: float, leverage: float) -> float:
    """
    Рассчитывает новый стоп-лосс в зависимости от направления сделки.

    :param entry_price: цена входа
    :param action: 'Buy' или 'Sell'
    :param stoploss_percent: процент стоп-лосса
    :param leverage: кредитное плечо
    :return: новая цена стоп-лосса
    """
    if str(action) == 'Buy':
        return float(entry_price) * (((stoploss_percent / leverage) / 100) + 1)
    elif str(action) == 'Sell':
        return float(entry_price) * (1 - ((stoploss_percent / leverage) / 100))
    else:
        return float(entry_price)


def current_position_bybit(session, symbol: str):
    """
    Возвращает активную позицию по символу на Bybit.
    Возвращает: side ("long"/"short"), size (float), entry_price (float)
    """
    try:
        resp = session.get_positions(category="linear", symbol=symbol)
        positions = resp.get("result", {}).get("list", [])
        
        for pos in positions:
            size = float(pos.get("size", 0))
            if size > 0:
                side = "long" if pos.get("side") == "Buy" else "short"
                entry_price = float(pos.get("avgPrice", 0))
                return side, size, entry_price

    except Exception as e:
        print(f"Error receiving position from Bybit: {e}")

    return None, 0.0, 0.0

while True:
    _, size_cur, avg_price = current_position_bybit(session, 'HEIUSDT')
    print("Remaining amount from the position:", size_cur, avg_price)

    if size_cur <= max(0, initial_qty - tp_qty * 0.99):
        print("✅ The first take was successfully completed.")
        break

    time.sleep(1)
    
new_stop_loss = calculate_new_stoploss(entry_price, action, stoploss_fist, NOW_LEVERAGE)
    
stop_resp = session.set_trading_stop(
    category="linear",
    symbol='HEIUSDT',
    side=closing_side,
    stopLoss=new_stop_loss,
    positionIdx=0
)
print("Stop loss updated:", stop_resp)
sendMessageToTelegram(BOT_API_KEY, ANDEJ_CHAT_ID, f'HEIUSDT Stop loss moved to level: {new_stop_loss}')