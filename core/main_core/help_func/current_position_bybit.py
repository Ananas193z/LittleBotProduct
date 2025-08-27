from pybit.unified_trading import HTTP
import time

from core.config import API_KEY, API_SECRET, FIRST_STOPLOSS, PLECHO, BOT_API_KEY, ANDEJ_CHAT_ID
from logs import sendMessageToTelegram

session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)

initial_qty = 11736.0
tp_qty = 0.4798
action = 'Buy'
closing_side = 'Sell'

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
        print(f"Ошибка при получении позиции Bybit: {e}")

    return None, 0.0, 0.0
#
# while True:
#     _, size_cur, avg_price = current_position_bybit(session, 'HEIUSDT')
#     print("Остаток позиции:", size_cur, avg_price)
#
#     # Проверяем, что почти весь объём тейкнут
#     if size_cur <= max(0, initial_qty - tp_qty * 0.99):
#         print("✅ Первый тейк успешно исполнен")
#         break
#
#     time.sleep(1)
#
# if str(action) == 'Buy':
#     new_stop_loss = float(avg_price) * (((FIRST_STOPLOSS / PLECHO) / 100) + 1)
# elif str(action) == 'Sell':
#     new_stop_loss = float(avg_price) * (1 - ((FIRST_STOPLOSS / PLECHO) / 100))
# else:
#     new_stop_loss = float(avg_price)
#
# stop_resp = session.set_trading_stop(
#     category="linear",
#     symbol='HEIUSDT',
#     side=closing_side,
#     stopLoss=new_stop_loss,
#     positionIdx=0
# )
# print("Стоп-лосс обновлён:", stop_resp)
# sendMessageToTelegram(BOT_API_KEY, ANDEJ_CHAT_ID, f'HEIUSDT Стоп лосс перемещён на уровень: {new_stop_loss}')