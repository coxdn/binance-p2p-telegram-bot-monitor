# Binance P2P Telegram Bot Monitor

This project provides a Telegram bot for monitoring Binance P2P orders by user nickname or rate/price.

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
byrate - Start monitoring orders by rate/price
list - List orders by current settings
stop - Stop monitoring
```

## Example

Start the bot by providing your Telegram bot token:
```bash
python main.py <YOUR_TELEGRAM_BOT_TOKEN>
```

The bot will guide you through setting up monitoring by user nickname or rate/price.

## Notes

- Make sure your bot is properly set up with the correct permissions to receive messages and respond to commands.
- This bot is intended for educational and informational purposes only. Use it responsibly.
