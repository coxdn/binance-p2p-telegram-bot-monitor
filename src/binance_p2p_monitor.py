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

    def get_p2p_orders(self, trans_amount=None, pay_type=None):
        url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "asset": self.asset,
            "fiat": self.fiat,
            "page": 1,
            "rows": self.rows,
            "tradeType": self.trade_type,
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

    def list_users(self, chat_id, trans_amount):
        return self._extract_banks_or_users(chat_id, key='users', trans_amount=trans_amount, extractor=lambda order: [
            (order['advertiser']['nickName'], order['adv']['price'])])

    def _extract_banks_or_users(self, chat_id, key, extractor, trans_amount=None):
        orders = self.get_p2p_orders(trans_amount=trans_amount, pay_type=self.user_data[chat_id].get('pay_type'))
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

    def start_monitoring(self, chat_id, target_user, notify_func):
        self._start_monitoring(chat_id, 'user', target_user, notify_func, self._monitor_orders)

    def start_rate_monitoring(self, chat_id, target_rate, notify_func):
        self._start_monitoring(chat_id, 'rate', target_rate, notify_func, self._monitor_rates)

    def _start_monitoring(self, chat_id, target_key, target_value, notify_func, monitor_method):
        self.user_data[chat_id][f'target_{target_key}'] = target_value
        self.user_data[chat_id]['is_monitoring'] = True
        Thread(target=monitor_method, args=(chat_id, notify_func)).start()

    def stop_monitoring(self, chat_id):
        self.user_data[chat_id]['is_monitoring'] = False

    def stop_rate_monitoring(self, chat_id):
        self.user_data[chat_id]['is_monitoring_rate'] = False

    def _monitor_orders(self, chat_id, notify_func):
        while self.user_data[chat_id]['is_monitoring']:
            orders = self.get_p2p_orders(
                trans_amount=self.user_data[chat_id].get('trans_amount'),
                pay_type=self.user_data[chat_id].get('pay_type')
            )

            if orders is None:
                notify_func(chat_id, 'Error fetching orders from Binance.')
                time.sleep(3)
                continue

            user_order = next((
                order for order in orders if order['advertiser']['nickName'] == self.user_data[chat_id]['target_user']
            ), None)

            if user_order and not self.user_data[chat_id]['target_order']:
                self.user_data[chat_id]['target_order'] = user_order
                notify_func(
                    chat_id,
                    f'Found an order from user {self.user_data[chat_id]["target_user"]}: '
                    f'{self.user_data[chat_id]["target_order"]["adv"]["price"]}')
            elif not user_order and self.user_data[chat_id]['target_order']:
                notify_func(chat_id, f'The order from user {self.user_data[chat_id]["target_user"]} has disappeared.')
                self.stop_monitoring(chat_id)
                break

            time.sleep(3)

    def _monitor_rates(self, chat_id, notify_func):
        while self.user_data[chat_id]['is_monitoring_rate']:
            orders = self.get_p2p_orders(
                trans_amount=self.user_data[chat_id].get('trans_amount'),
                pay_type=self.user_data[chat_id].get('pay_type')
            )

            if orders is None:
                notify_func(chat_id, 'Error fetching orders from Binance.')
                time.sleep(3)
                continue

            if not orders:
                time.sleep(3)
                continue

            first_order_price = float(orders[0]['adv']['price'])
            target_rate = float(self.user_data[chat_id]['target_rate'])

            if (self.user_data[chat_id]['trade_type'] == 'SELL' and first_order_price <= target_rate) or \
                    (self.user_data[chat_id]['trade_type'] == 'BUY' and first_order_price >= target_rate):
                notify_func(chat_id, f'Order matching the rate {target_rate} found: {first_order_price}')
                self.stop_rate_monitoring(chat_id)

            time.sleep(3)
