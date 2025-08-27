from pybit.unified_trading import HTTP
from bybitchecker import get_price_from_bybit, get_aleivebel_balance
from trading_startegy import monitor_and_update_stop, has_position
import time

API_KEY           = "KgAb27DWwLEHm3t9xe"
API_SECRET        = "ynTuNqzi8tB7Li7PnMxPtlULr12DyHBkG8sa"
balancebybit      = 10000
PLECHO            = 20
nowprcentforstart = 10
trading_pair      = 'FARTCOINUSDT'
side              = 'Sell'

entry_price       = 1.131
tp_profits        = [1.12, 1.11, 1.10, 1.09]
prcents           = [10, 18, 21.5, 100]
stoploss_fist     = 20

tp_price          = tp_profits[3]
sl_price          = 1.2

realprice = get_price_from_bybit(trading_pair)
amountforstart = round((float(balancebybit) * (nowprcentforstart / 100)), 2)
doladlastartafiltered = int(round((amountforstart/realprice), 0) * int(PLECHO))

if realprice <= entry_price:
    triggerDirection = 1
else:
    triggerDirection = 2
                
session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)

order = {
    "category": "linear",
    "symbol": trading_pair,
    "side": side,
    "orderType": "Limit",
    "qty": doladlastartafiltered,

    # Лимит-цена, по которой разместится ордер ПОСЛЕ триггера:
    "price": str(entry_price),

    # Делаем ордер УСЛОВНЫМ (stop-entry):
    "triggerPrice": str(entry_price),
    "triggerDirection": triggerDirection,     # 1 = если цена ПОД твх, 2 = если цена НАД твх
    "triggerBy": "LastPrice",      # можно "MarkPrice" если хочешь меньше фитилей

    "timeInForce": "GTC",

    # TP/SL сразу на позицию (Unified):
    "takeProfit": str(tp_price),
    "stopLoss": str(sl_price),
    "tpTriggerBy": "LastPrice",
    "slTriggerBy": "LastPrice",

    # Полный режим TP/SL (на всю позицию). Для Full tp/sl должны быть Market.
    "tpslMode": "Full",
    "tpOrderType": "Market",
    "slOrderType": "Market",

    # Режим позиций:
    "positionIdx": 0,              # 0=one-way; 1=hedge long; 2=hedge short
    "reduceOnly": False,           # Открываем, а не закрываем
    # "orderLinkId": "btc_entry_110k_001",  # опционально: свой ID
}

resp = session.place_order(**order)
start_order_id = resp["result"]["orderId"]
print(start_order_id)

while True:
    if has_position(session, trading_pair):
        print('Позиция открылась!!!')
        break
    else:
        print('Ордер ещё не исполнен')
    time.sleep(1)
    
monitor_and_update_stop(session, trading_pair, side, doladlastartafiltered, tp_profits, prcents, stoploss_fist, entry_price, start_order_id)
