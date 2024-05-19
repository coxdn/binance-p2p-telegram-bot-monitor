from src.binance_p2p_monitor import BinanceP2PMonitor
from src.telegram_bot import TelegramBot
import sys


if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        print("Usage: python main.py <TOKEN>")
        print("You need to provide the Telegram bot token as an argument.")
        sys.exit(1)

    monitor = BinanceP2PMonitor()
    bot = TelegramBot(TOKEN, monitor)
    bot.run()
