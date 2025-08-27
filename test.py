import re
from pybit.unified_trading import HTTP
from bybitchecker import get_price_from_bybit
from config import *
from trading_utils import current_position_bybit

session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)

resp = session.get_instruments_info(category="linear", symbol='ALPHAUSDT')
filters = resp["result"]["list"][0]["lotSizeFilter"]
max_qty = int(filters["maxMktOrderQty"])  # Количество контрактов, которое разрешено выставить в MARKET

print(max_qty)
print(595940)

print(595940/max_qty)