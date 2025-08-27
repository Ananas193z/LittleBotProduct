import re
import json

text = '''
🔥 #FIL/USDT (Long📈, x20) 🔥

Entry - 2.702
Take-Profit:

🥉 2.756 (40% of profit)
🥈 2.7831 (60% of profit)
🥇 2.8101 (80% of profit)
🚀 2.8371 (100% of profit)
'''

def parse_signal(text: str):
    # Убираем все ** жирности
    cleaned = re.sub(r'\*\*+', '', text)

    # Заголовок
    header_match = re.search(r'#([A-Z]+)/([A-Z]+)\s+\((Long|Short)[^,]*,\s*x(\d+)\)', cleaned)
    if not header_match:
        raise ValueError("Не удалось найти заголовок сигнала")

    symbol = f"{header_match.group(1)}{header_match.group(2)}".upper()
    direction = "Buy" if header_match.group(3).lower() == "long" else "Sell"
    leverage = int(header_match.group(4))

    # Точка входа
    entry_match = re.search(r'Entry\s*-\s*([\d.]+)', cleaned)
    if not entry_match:
        raise ValueError("Не найдена точка входа")
    entry_price = float(entry_match.group(1))

    # Тейк-профиты
    tp_matches = re.findall(r'([🚀🥇🥈🥉])\s*([\d.]+)\s*\((\d+)% of profit\)', cleaned)
    take_profits = []
    for emoji, price, percent in tp_matches:
        take_profits.append({
            "level": emoji,
            "price": float(price),
            "percent": int(percent)
        })

    return {
        "symbol": symbol,
        "side": direction,
        "leverage": leverage,
        "entry": entry_price,
        "take_profits": take_profits
    }

if __name__ == '__main__':
    result = parse_signal(text)
    print(json.dumps(result, indent=2))
