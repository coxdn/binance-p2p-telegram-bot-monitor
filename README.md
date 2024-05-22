# Binance P2P Telegram Bot Monitor

This Telegram bot for monitoring Binance P2P orders by user nickname or price. It was created because push notifications from the Binance app sometimes do not work on certain phones, requiring users to constantly check their phones to see if their order has been fulfilled. The bot monitors the specified order and notifies the subscribed user when the order disappears. It can also monitor when the price crosses a specified price, depending on the buy or sell section.

## Installation

Clone the repository and navigate to the project directory.
```bash
git clone https://github.com/coxdn/binance-p2p-monitor.git
cd binance-p2p-monitor
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the bot with your Telegram bot token:
```bash
python main.py <TOKEN>
```

If you run the script without providing a token, you will see the following message:
```
Usage: python main.py <TOKEN>
You need to provide the Telegram bot token as an argument.
```

## Telegram Bot Commands

Configure the following commands in your Telegram bot:
```
start - Displays instructions on how to use the bot
bynick - Start monitoring orders by user nickname
byprice - Start monitoring orders by price
list - List orders by current settings
status - Show current monitoring status
stop - Stop monitoring
```

## Example

Start the bot by providing your Telegram bot token:
```bash
python main.py <YOUR_TELEGRAM_BOT_TOKEN>
```

The bot will guide you through setting up monitoring by user nickname or price.

## Notes

- Make sure your bot is properly set up with the correct permissions to receive messages and respond to commands.
- This bot is intended for educational and informational purposes only. Use it responsibly.
