import requests
from config import BOT_API_KEY, ANDEJ_CHAT_ID
import threading

def notify_async(message: str):
    threading.Thread(
        target=sendMessageToTelegram,
        args=(BOT_API_KEY, ANDEJ_CHAT_ID, message)
    ).start()

def sendMessageToTelegram(token: str, chat_id: int, message: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Сообщение успешно отправлено.")
        else:
            print("❌ Ошибка при отправке:", response.text)
    except Exception as e:
        print("⚠️ Ошибка запроса:", e)
