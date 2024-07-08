import logging
import os
from kiteconnect import KiteConnect
from config import KITE_API_KEY, KITE_API_SECRET, PRODUCT_TYPE, ORDER_TYPE, SLP, TP
from utils import write_order_data_to_file, write_missed_order_data_to_file

logger = logging.getLogger(__name__)


def calculate_target_price(price):
    """
    Calculate the target price by increasing the current price by a specified percentage and rounding to the nearest 0.05.
    :param price: Current price
    :param increment_percentage: Percentage to increase the price
    :return: Target price rounded to the nearest 0.05
    """
    increased_price = price * (1 + TP / 100)
    target_price = round(increased_price / 0.05) * 0.05
    return target_price

def calculate_stop_loss_price(price):
    """
    Calculate the stop loss price by decreasing the current price by a specified percentage and rounding to the nearest 0.05.
    :param price: Current price
    :param decrement_percentage: Percentage to decrease the price
    :return: Stop loss price rounded to the nearest 0.05
    """
    decreased_price = price * (1 - SLP / 100)
    stop_loss_price = round(decreased_price / 0.05) * 0.05
    return stop_loss_price


def _get_quantity(balance, price):
    try:
        return (int(balance / price) - 1) if balance >= price else 0
    except Exception as e:
        logger.error(f"Error calculating quantity: {e}")
        return 0


class KiteService:
    def __init__(self):
        self.kite = None
        self.access_token_file = 'access_token.txt'
        self.api_key = KITE_API_KEY
        self.api_secret = KITE_API_SECRET
        self.kite = KiteConnect(api_key=self.api_key)
        self._initialize_session()

    def _initialize_session(self):
        try:
            access_token = self._get_saved_access_token()
            if access_token:
                self.kite.set_access_token(access_token)
                logger.info("Access token found and session initialized.")
            else:
                logger.error("No access token found. Please login first.")
                raise Exception("No access token found. Please login first.")
        except Exception as e:
            logger.error(f"Error initializing session: {e}")

    def generate_kite_session(self, request_token=None):
        try:
            if request_token:
                data = self.kite.generate_session(request_token, api_secret=self.api_secret)
                self.kite.set_access_token(data["access_token"])
                self._save_access_token(data["access_token"])
                logger.info("New Kite session generated.")
            else:
                logger.warning("Request token not provided.")
        except Exception as e:
            logger.error(f"Error generating Kite session: {e}")

    def _save_access_token(self, token):
        try:
            with open(self.access_token_file, 'w') as f:
                f.write(token)
            logger.info("Access token saved.")
        except Exception as e:
            logger.error(f"Error saving access token: {e}")

    def _get_saved_access_token(self):
        try:
            if os.path.exists(self.access_token_file):
                with open(self.access_token_file, 'r') as f:
                    token = f.read().strip()
                logger.info("Access token retrieved from file.")
                return token
            return None
        except Exception as e:
            logger.error(f"Error retrieving access token: {e}")
            return None

    def create_primary_order(self, symbol, quantity, price, transaction_type, order_type):
        try:
            if order_type == 'LIMIT':
                return self.create_limit_order(symbol, quantity, price, transaction_type, order_type)
            else:
                return self.kite.place_order(tradingsymbol=symbol, exchange=self.kite.EXCHANGE_NSE,
                                             transaction_type=transaction_type, quantity=quantity,
                                             variety=self.kite.VARIETY_REGULAR,
                                             order_type=self.kite.ORDER_TYPE_MARKET, product=PRODUCT_TYPE,
                                             validity=self.kite.VALIDITY_DAY)
        except Exception as e:
            logger.error(f"Error creating primary order: {e}")

    def create_limit_order(self, symbol, quantity, price, transaction_type, order_type):
        try:
            return self.kite.place_order(tradingsymbol=symbol, exchange=self.kite.EXCHANGE_NSE,
                                         transaction_type=transaction_type, quantity=quantity, price=price,
                                         variety=self.kite.VARIETY_REGULAR,
                                         order_type=order_type, product=PRODUCT_TYPE,
                                         validity=self.kite.VALIDITY_DAY)
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")

    def create_sl_order(self, symbol, quantity, price, transaction_type, order_type):
        try:
            return self.kite.place_order(tradingsymbol=symbol, exchange=self.kite.EXCHANGE_NSE,
                                         transaction_type=transaction_type, quantity=quantity, trigger_price=price,
                                         variety=self.kite.VARIETY_REGULAR,
                                         order_type=order_type, product=PRODUCT_TYPE,
                                         validity=self.kite.VALIDITY_DAY)
        except Exception as e:
            logger.error(f"Error creating stop-loss order: {e}")

    def place_order(self, data):
        if not self.kite:
            raise Exception("Kite session not generated")

        symbol = data.get('TS')
        if not symbol:
            raise Exception("Symbol not provided")
        logger.info(f"Margins {self.kite.margins()}")
        total_cash = self.kite.margins()['equity']['available']['live_balance']
        # stock_ltp = self._get_stock_ltp(symbol)
        price = float(data['PRICE']) if data['PRICE'] else self._get_stock_ltp(symbol)
        target_price = _calculate_target_price(price)
        stop_loss_price = _calculate_stop_loss_price(price)
        try:
            quantity = _get_quantity(total_cash, price)
            if quantity < 1:
                raise Exception("Quantity cannot be 0")
            primary_transaction_type = 'SELL' if data['TT'] == 'SELL' else 'BUY'
            primary_order_type = ORDER_TYPE

            target_transaction_type = 'BUY' if primary_transaction_type == 'SELL' else 'SELL'
            target_order_type = 'LIMIT'

            stop_loss_transaction_type = 'BUY' if primary_transaction_type == 'SELL' else 'SELL'
            stop_loss_order_type = 'SL-M'

            logger.info(f"Placing order : Cash Balance {total_cash}, Stock {symbol}, "
                        f"Last Traded Price: {price}, Quantity: {quantity}")

            primary_order_id = self.create_primary_order(symbol, quantity, price, primary_transaction_type,
                                                         primary_order_type)
            target_order_id = self.create_limit_order(symbol, quantity, target_price, target_transaction_type,
                                                      target_order_type)
            sl_order_id = self.create_sl_order(symbol, quantity, stop_loss_price, stop_loss_transaction_type,
                                               stop_loss_order_type)

            primary_order = self.kite.order_history(order_id=primary_order_id)
            target_order = self.kite.order_history(order_id=target_order_id)
            sl_order = self.kite.order_history(order_id=sl_order_id)
            write_order_data_to_file(primary_order_id, [primary_order, target_order, sl_order])

            logger.info(f"Order placed successfully: {primary_order_id}, {target_order_id}, {sl_order_id}")
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            write_missed_order_data_to_file(data, price, target_price, stop_loss_price)

    def _get_stock_ltp(self, symbol):
        try:
            return self.kite.quote(f'NSE:{symbol}')[f'NSE:{symbol}']['last_price']
        except Exception as e:
            logger.error(f"Error getting stock LTP: {e}")
