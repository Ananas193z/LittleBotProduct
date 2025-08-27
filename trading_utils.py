import time
from config import *
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta

def has_position(session, symbol: str) -> bool:
    """
    Возвращает True, если по символу открыта любая позиция (size > 0).
    """
    try:
        r = session.get_positions(category="linear", symbol=symbol)
        items = (r.get("result", {}) or {}).get("list", []) or []
        for p in items:
            size = float(p.get("size") or 0)
            if size > 0:
                return True
        return False
    except Exception as e:
        print(f"Ошибка при запросе позиции: {e}")
        return False

def get_closed_pnl(session, symbol: str, start_ts_ms: int, end_ts_ms: int) -> list:
    """
    Возвращает список закрытых сделок с PnL по символу за указанный период.
    """
    try:
        resp = session.get_closed_pnl(
            category="linear",
            symbol=symbol.upper(),
            startTime=start_ts_ms,
            endTime=end_ts_ms,
            limit=50
        )
        return resp.get("result", {}).get("list", []) or []
    except Exception as e:
        print("Ошибка при получении closed PnL:", e)
        return []
    
def check_order_status(session, order_id, symbol):
    """
    Получает статус ордера по order_id через REST API.
    Возвращает значение поля orderStatus, например, "Filled", "New" и т.п.
    """
    try:
        response = session.get_open_orders(category="linear", symbol=symbol, order_id=order_id)
        if response["result"]["list"]:
            status = response["result"]["list"][0]["orderStatus"]
            print("STATUS OF ORDER:", status, order_id)
            return status
        else:
            print("Ордер не найден среди открытых (вероятно, исполнен).")
            return "Filled"
    except Exception as e:
        print(f"Исключение при получении открытых ордеров: {e}")
        return None

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