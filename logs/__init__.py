# Makes 'logs' a Python package
from .telegram_send_logs import notify_async, sendMessageToTelegram

__all__ = ['notify_async', 'sendMessageToTelegram']