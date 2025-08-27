from telethon import TelegramClient, events
from pybit.unified_trading import HTTP
from parse_utils import parse_signal
from bybit_main import start_traiding
import threading
from config import *



session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET)

client = TelegramClient("session_name", API_ID, API_HASH)


async def main():
    # Вход в аккаунт, если требуется
    await client.start(PHONE_NUMBER)
    print("Бот запущен и слушает канал...")

    @client.on(events.NewMessage(chats=CHANNEL_ID))
    async def new_message_handler(event):
        """Обработчик новых сообщений в канале"""
        now_message_id = event.message.id
        #print(f"[{event.message.date}] {event.chat.title}")
        print("11111111111111111111111111111111111111111")
        print(now_message_id)
        print(f'{event.message.text}')
        
        try:
            signal_data = parse_signal(str(event.message.text))
        except:
            signal_data = None
            
        print(signal_data)

        if signal_data != None:
            threading.Thread(
                target=start_traiding,
                args=(session, str(event.message.text), signal_data)
            ).start()
        else:
            print('Это не сигнал')
    
    
    await client.run_until_disconnected()
    

client.loop.run_until_complete(main())