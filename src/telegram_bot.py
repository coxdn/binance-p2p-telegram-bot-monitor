import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class TelegramBot:
    def __init__(self, token, monitor):
        self.bot = telebot.TeleBot(token)
        self.monitor = monitor

        # Setup command handlers
        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(commands=['bynick'])(self.by_nick)
        self.bot.message_handler(commands=['byrate'])(self.by_rate)
        self.bot.message_handler(commands=['stop'])(self.stop_monitoring)
        self.bot.message_handler(commands=['list'])(self.list_orders)

        # Setup callback handlers
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('trade_type'))(self.set_trade_type)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('amount'))(self.set_amount)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('bank'))(self.set_bank)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('user'))(self.set_user)

    def initialize_user_data(self, chat_id):
        if chat_id not in self.monitor.user_data:
            self.monitor.user_data[chat_id] = {
                'is_monitoring': False, 'target_user': None, 'target_order': None,
                'trade_type': None, 'trans_amount': None, 'pay_type': None,
                'banks': [], 'users': [], 'target_rate': None, 'is_monitoring_rate': False,
                'command': None}

    def start(self, message):
        chat_id = message.chat.id
        self.initialize_user_data(chat_id)
        self.bot.reply_to(
            message,
            'Hello! Use /bynick to monitor orders by user nickname or /byrate to monitor orders by rate. '
            'Choose one of them to start.')

    def by_nick(self, message):
        self.prepare_for_monitoring(message, 'bynick')

    def by_rate(self, message):
        self.prepare_for_monitoring(message, 'byrate')

    def prepare_for_monitoring(self, message, command):
        chat_id = message.chat.id
        self.initialize_user_data(chat_id)

        # Stop any ongoing monitoring
        if self.monitor.user_data[chat_id]['is_monitoring'] or self.monitor.user_data[chat_id]['is_monitoring_rate']:
            self.monitor.stop_monitoring(chat_id)
            self.monitor.stop_rate_monitoring(chat_id)
            self.bot.send_message(chat_id, 'Previous monitoring stopped.')

        self.monitor.user_data[chat_id]['command'] = command
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('BUY', callback_data='trade_type:BUY'))
        markup.add(InlineKeyboardButton('SELL', callback_data='trade_type:SELL'))
        self.bot.send_message(chat_id, 'Select trade type:', reply_markup=markup)

    def set_trade_type(self, call):
        chat_id = call.message.chat.id
        trade_type = call.data.split(':')[1]
        self.monitor.user_data[chat_id]['trade_type'] = trade_type
        self.bot.send_message(chat_id, f'Trade type set to: {trade_type}')
        self.show_amounts(chat_id)

    def show_amounts(self, chat_id):
        markup = InlineKeyboardMarkup()
        amounts = [5000, 5500, 6000, 6500, 7000, 7100, 7200, 7300, 7400, 7500, 7600, 8000]
        for amount in amounts:
            markup.add(InlineKeyboardButton(str(amount), callback_data=f'amount:{amount}'))
        markup.add(InlineKeyboardButton('Custom', callback_data='amount:Custom'))
        self.bot.send_message(chat_id, 'Select amount:', reply_markup=markup)

    def set_amount(self, call):
        chat_id = call.message.chat.id
        amount = call.data.split(':')[1]
        if amount == 'Custom':
            self.bot.send_message(chat_id, 'Please enter the custom amount:')
            self.bot.register_next_step_handler(call.message, self.custom_amount)
        else:
            self.monitor.user_data[chat_id]['trans_amount'] = amount
            self.bot.send_message(chat_id, f'Amount set to: {amount}')
            self.show_banks(chat_id)

    def custom_amount(self, message):
        chat_id = message.chat.id
        try:
            amount = float(message.text)
            self.monitor.user_data[chat_id]['trans_amount'] = amount
            self.bot.send_message(chat_id, f'Custom amount set to: {amount}')
            self.show_banks(chat_id)
        except ValueError:
            self.bot.reply_to(message, 'Invalid amount. Please enter a number.')

    def show_banks(self, chat_id):
        banks = self.monitor.list_banks(chat_id)
        markup = InlineKeyboardMarkup()
        for bank in banks:
            markup.add(InlineKeyboardButton(bank, callback_data=f'bank:{bank}'))
        markup.add(InlineKeyboardButton('Custom', callback_data='bank:Custom'))
        self.bot.send_message(chat_id, 'Select bank:', reply_markup=markup)

    def set_bank(self, call):
        chat_id = call.message.chat.id
        bank = call.data.split(':')[1]
        if bank == 'Custom':
            self.bot.send_message(chat_id, 'Please enter the custom bank identifier:')
            self.bot.register_next_step_handler(call.message, self.custom_bank)
        else:
            self.monitor.user_data[chat_id]['pay_type'] = bank
            self.bot.send_message(chat_id, f'Bank set to: {bank}')
            self.process_command(chat_id)

    def custom_bank(self, message):
        chat_id = message.chat.id
        bank = message.text
        self.monitor.user_data[chat_id]['pay_type'] = bank
        self.bot.send_message(chat_id, f'Custom bank identifier set to: {bank}')
        self.process_command(chat_id)

    def process_command(self, chat_id):
        command = self.monitor.user_data[chat_id]['command']
        if command == 'bynick':
            self.show_users(chat_id)
        elif command == 'byrate':
            self.show_rate_input(chat_id)

    def show_users(self, chat_id):
        users = self.monitor.list_users(chat_id, self.monitor.user_data[chat_id]['trans_amount'])
        markup = InlineKeyboardMarkup()
        for user, price in users:
            markup.add(InlineKeyboardButton(f'{user} ({price})', callback_data=f'user:{user}'))
        self.bot.send_message(chat_id, 'Select user:', reply_markup=markup)

    def set_user(self, call):
        chat_id = call.message.chat.id
        user = call.data.split(':')[1]
        self.monitor.user_data[chat_id]['target_user'] = user
        self.bot.send_message(chat_id, f'User set to: {user}')
        self.start_monitoring_by_nick(chat_id)

    def show_rate_input(self, chat_id):
        self.bot.send_message(chat_id, 'Please enter the target rate (e.g., 40.34):')
        self.bot.register_next_step_handler_by_chat_id(chat_id, self.set_rate)

    def set_rate(self, message):
        chat_id = message.chat.id
        try:
            rate = float(message.text)
            self.monitor.user_data[chat_id]['target_rate'] = rate
            self.bot.send_message(chat_id, f'Rate set to: {rate}')
            self.start_monitoring_by_rate(chat_id)
        except ValueError:
            self.bot.reply_to(message, 'Invalid rate. Please enter a number.')

    def start_monitoring_by_nick(self, chat_id):
        user = self.monitor.user_data[chat_id]['target_user']
        self.monitor.start_monitoring(chat_id, user, self.notify)
        self.bot.send_message(chat_id, f'Monitoring started for user: {user}')

    def start_monitoring_by_rate(self, chat_id):
        rate = self.monitor.user_data[chat_id]['target_rate']
        self.monitor.start_rate_monitoring(chat_id, rate, self.notify)
        self.bot.send_message(chat_id, f'Monitoring started for rate: {rate}')

    def notify(self, chat_id, msg):
        self.bot.send_message(chat_id, msg)

    def stop_monitoring(self, message):
        chat_id = message.chat.id
        if chat_id in self.monitor.user_data:
            self.monitor.stop_monitoring(chat_id)
            self.monitor.stop_rate_monitoring(chat_id)
            self.bot.send_message(chat_id, 'Monitoring has been stopped.')
        else:
            self.bot.send_message(chat_id, 'No active monitoring found.')

    def list_orders(self, message):
        chat_id = message.chat.id
        self.initialize_user_data(chat_id)

        orders = self.monitor.get_p2p_orders(
            trans_amount=self.monitor.user_data[chat_id].get('trans_amount'),
            pay_type=self.monitor.user_data[chat_id].get('pay_type')
        )

        if not orders:
            self.bot.send_message(chat_id, 'No orders found.')
            return

        response = "\n".join([f"{order['adv']['price']} - {order['advertiser']['nickName']}" for order in orders])
        self.bot.send_message(chat_id, response)

    def run(self):
        self.bot.polling()
