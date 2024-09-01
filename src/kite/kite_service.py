import json
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from flask import Flask
from kiteconnect import KiteConnect

from src.config import KITE_API_KEY, KITE_API_SECRET, PRODUCT_TYPE, ORDER_TYPE, SLP, TP
from src.data.selected_nifty_companies import selected_companies
from src.indicators import get_indicators
from src.utils.util import save_to_csv, write_order_data_to_file, write_missed_order_data_to_file

logger = logging.getLogger(__name__)
app = Flask(__name__)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def _calculate_target_price(price):
    """
    Calculate the target price by increasing the current price by a specified percentage and rounding to the nearest 0.05.
    :param price: Current price
    :param increment_percentage: Percentage to increase the price
    :return: Target price rounded to the nearest 0.05
    """
    increased_price = price * (1 + TP / 100)
    target_price = round(increased_price / 0.05) * 0.05
    return target_price


def _calculate_stop_loss_price(price):
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
        price = float(data['PRICE']) if data['PRICE'] else self._get_stock_ltp(symbol)
        target_price = _calculate_target_price(price)
        stop_loss_price = _calculate_stop_loss_price(price)
        try:
            quantity = int(data['QTY']) if data.get('QTY') else _get_quantity(total_cash, price)
            if quantity < 1:
                raise Exception("Quantity cannot be 0")

            primary_transaction_type = 'SELL' if data['TT'] == 'SELL' else 'SELL'
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

    def save_instruments_to_file(self):
        """
        Fetch instruments data from the Kite API and save it to a file named 'nifty_data.json'.
        """
        # Fetch the instruments data
        instruments_data = self.kite.instruments(exchange=self.kite.EXCHANGE_NSE)

        # Define the file name
        file_name = 'nifty_data.json'

        # Write the data to the file in JSON format
        with open(file_name, 'w') as file:
            json.dump(instruments_data, file, indent=4)

        print(f"Data successfully written to {file_name}")

    @staticmethod
    def get_instruments():
        file_name = 'nifty_data.json'
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data

    # def get_historical_data(self, interval: str = '15minute', delta: int = 7):
    #     # Get the current date and time
    #     to_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #
    #     # Calculate the 'from_date' by subtracting the delta days and include time
    #     from_date = (datetime.now() - timedelta(days=delta)).strftime('%Y-%m-%d %H:%M:%S')
    #
    #     nifty_list = [key for key in self.get_instruments() if key['tradingsymbol'] in selected_companies.keys()]
    #     for symbol in nifty_list:
    #         try:
    #             historical_data = self.kite.historical_data(symbol['instrument_token'], from_date,
    #                                                         to_date, interval)
    #             df = pd.DataFrame(historical_data)
    #
    #             response = get_indicators(df)
    #             response = response[50:]
    #             save_to_csv(response, symbol['tradingsymbol'])
    #             logger.info(f"Got historical data for {symbol['tradingsymbol']}")
    #         except Exception as e:
    #             logger.error(f"Error getting historical data: {e}")
    #             return None
    #         break

    def get_historical_data_for_stock(self, ticker_symbol: str, interval: str = '15minute', delta: int = 7):
        if not ticker_symbol:
            raise Exception("Ticker symbol not provided")
        # Get the current date and time
        to_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Calculate the 'from_date' by subtracting the delta days and include time
        from_date = (datetime.now() - timedelta(days=delta)).strftime('%Y-%m-%d %H:%M:%S')

        symbol = [_ for _ in self.get_instruments() if _['tradingsymbol'] == ticker_symbol][0]

        try:
            historical_data = self.kite.historical_data(symbol['instrument_token'], from_date,
                                                        to_date, interval)
            df = pd.DataFrame(historical_data)

            response = get_indicators(df)
            response = response.iloc[-50:]
            result = self.dataframe_to_json(response)
            logger.info(f"Got historical data for {symbol['tradingsymbol']}")
            return result
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    @staticmethod
    def dataframe_to_json(df):
        """
        Convert a pandas DataFrame to JSON format.

        Parameters:
        df (pd.DataFrame): The DataFrame to convert.

        Returns:
        str: JSON string representation of the DataFrame.
        """
        # Convert the DataFrame to JSON format
        json_result = df.to_json(orient='records', date_format='iso')

        return json_result


if __name__ == '__main__':
    kite = KiteService()
    kite.get_historical_data()
