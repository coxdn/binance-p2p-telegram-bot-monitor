import requests
import time
from threading import Thread


class BinanceP2PMonitor:
    def __init__(self, asset='USDT', fiat='UAH', trade_type='BUY', rows=20):
        self.asset = asset
        self.fiat = fiat
        self.trade_type = trade_type
        self.rows = rows
        self.user_data = {}

    def get_p2p_orders(self, chat_id):
        url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
        headers = {
            'Content-Type': 'application/json'
        }

        trade_type = self.user_data[chat_id].get('trade_type')
        trans_amount = self.user_data[chat_id].get('trans_amount')
        pay_type = self.user_data[chat_id].get('pay_type')

        data = {
            "asset": self.asset,
            "fiat": self.fiat,
            "page": 1,
            "rows": self.rows,
            "tradeType": trade_type if trade_type else self.trade_type,
            "transAmount": trans_amount if trans_amount else "",
            "payTypes": [pay_type] if pay_type else [],
            "publisherType": None
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.RequestException:
            return None

    def list_banks(self, chat_id):
        return self._extract_banks_or_users(chat_id, key='banks', extractor=lambda order: [tm['identifier'] for tm in
                                                                                           order['adv'][
                                                                                               'tradeMethods']])

    def list_nicknames(self, chat_id):
        return self._extract_banks_or_users(chat_id, key='users', extractor=lambda order: [
            (order['advertiser']['nickName'], order['adv']['price'])])

    def _extract_banks_or_users(self, chat_id, key, extractor):
        orders = self.get_p2p_orders(chat_id)
        if orders is None:
            return []

        extracted = []
        seen = set()
        for order in orders:
            for item in extractor(order):
                if item not in seen:
                    extracted.append(item)
                    seen.add(item)

        self.user_data[chat_id][key] = extracted
        return self.user_data[chat_id][key]

    def start_nick_monitoring(self, chat_id, target_nick, notify_func):
        self._start_monitoring(chat_id, 'nick', target_nick, notify_func, self._monitor_orders)

    def start_price_monitoring(self, chat_id, target_price, notify_func):
        self._start_monitoring(chat_id, 'price', target_price, notify_func, self._monitor_prices)

    def _start_monitoring(self, chat_id, target_key, target_value, notify_func, monitor_method):
        self.user_data[chat_id][f'target_{target_key}'] = target_value
        self.user_data[chat_id]['is_monitoring'] = True
        Thread(target=monitor_method, args=(chat_id, notify_func)).start()

    def stop_monitoring(self, chat_id):
        self.user_data[chat_id]['is_monitoring'] = False

    def _monitor_orders(self, chat_id, notify_func):
        while self.user_data[chat_id]['is_monitoring']:
            orders = self.get_p2p_orders(chat_id)

            if orders is None:
                notify_func(chat_id, 'Error fetching orders from Binance.')
                time.sleep(3)
                continue

            user_order = next((
                order for order in orders if order['advertiser']['nickName'] == self.user_data[chat_id]['target_nick']
            ), None)

            if user_order and not self.user_data[chat_id]['target_order']:
                self.user_data[chat_id]['target_order'] = user_order
                notify_func(
                    chat_id,
                    f'Found an order from user {self.user_data[chat_id]["target_nick"]}: '
                    f'{self.user_data[chat_id]["target_order"]["adv"]["price"]}')
            elif not user_order and self.user_data[chat_id]['target_order']:
                notify_func(chat_id, f'The order from user {self.user_data[chat_id]["target_nick"]} has disappeared.')
                self.stop_monitoring(chat_id)
                break

            time.sleep(3)

    def _monitor_prices(self, chat_id, notify_func):
        while self.user_data[chat_id]['is_monitoring']:
            orders = self.get_p2p_orders(chat_id)

            if orders is None:
                notify_func(chat_id, 'Error fetching orders from Binance.')
                time.sleep(3)
                continue

            if not orders:
                time.sleep(3)
                continue

            first_order_price = float(orders[0]['adv']['price'])
            target_price = float(self.user_data[chat_id]['target_price'])
            trade_type = self.user_data[chat_id]['trade_type']

            if (trade_type == 'SELL' and first_order_price <= target_price) or \
                    (trade_type == 'BUY' and first_order_price >= target_price):
                notify_func(
                    chat_id,
                    f'Monitoring stopped: Order matching the price {target_price} found: {first_order_price}')
                self.stop_monitoring(chat_id)

            time.sleep(3)
