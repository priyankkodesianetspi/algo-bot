import upstox_client
from upstox_client.rest import ApiException
from upstox_client import OrderApi, HistoryApi, PlaceOrderRequest, ModifyOrderRequest
import config

class UpstoxOrderClient:
    def __init__(self, access_token):
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token
        self.api_client = upstox_client.ApiClient(configuration)
        self.order_api = OrderApi(self.api_client)
        self.history_api = HistoryApi(self.api_client)
        self.api_version = '2.0'

    def place_order(self, quantity, disclosed_quantity, duration, limit_price, product, instrument, order_type,
                    transaction_type, trigger_price, trailing_stop_loss, is_amo):
        body = PlaceOrderRequest(
            quantity=quantity,
            disclosed_quantity=disclosed_quantity,
            duration=duration,
            limit_price=limit_price,
            product=product,
            instrument=instrument,
            order_type=order_type,
            transaction_type=transaction_type,
            trigger_price=trigger_price,
            trailing_stop_loss=trailing_stop_loss,
            is_amo=is_amo
        )
        try:
            api_response = self.order_api.place_order(body, self.api_version)
            return api_response
        except ApiException as e:
            print(f"Exception when calling OrderApi->place_order: {e}\n")
            return None

    def modify_order(self, quantity, duration, order_id, order_type, trigger_price, disclosed_quantity, limit_price):
        body = ModifyOrderRequest(
            quantity=quantity,
            duration=duration,
            order_id=order_id,
            order_type=order_type,
            trigger_price=trigger_price,
            disclosed_quantity=disclosed_quantity,
            limit_price=limit_price
        )
        try:
            api_response = self.order_api.modify_order(body, self.api_version)
            return api_response
        except ApiException as e:
            print(f"Exception when calling OrderApi->modify_order: {e}\n")
            return None

    def cancel_order(self, order_id):
        try:
            api_response = self.order_api.cancel_order(order_id, self.api_version)
            return api_response
        except ApiException as e:
            print(f"Exception when calling OrderApi->cancel_order: {e}\n")
            return None

    def get_historical_candle_data(self, instrument_key, interval, to_date, from_date):
        try:
            api_response = self.history_api.get_historical_candle_data1(instrument_key, interval, to_date, from_date,
                                                                        self.api_version)
            return api_response
        except ApiException as e:
            print(f"Exception when calling HistoryApi->get_historical_candle_data: {e}\n")
            return None

    # Wrapper methods for buy, sell, target, and stop loss orders
    def place_buy_order(self, quantity, instrument, price=None, is_amo=False):
        return self.place_order(
            quantity=quantity,
            disclosed_quantity=0,
            duration="DAY",
            limit_price=price if price else 0.0,
            product="MIS",
            instrument=instrument,
            order_type="LIMIT" if price else "MARKET",
            transaction_type="BUY",
            trigger_price=0.0,
            trailing_stop_loss=0.0,
            is_amo=is_amo
        )

    def place_sell_order(self, quantity, instrument, price=None, is_amo=False):
        return self.place_order(
            quantity=quantity,
            disclosed_quantity=0,
            duration="DAY",
            limit_price=price if price else 0.0,
            product="MIS",
            instrument=instrument,
            order_type="LIMIT" if price else "MARKET",
            transaction_type="SELL",
            trigger_price=0.0,
            trailing_stop_loss=0.0,
            is_amo=is_amo
        )

    def place_target_order(self, quantity, instrument, target_price, transaction_type):
        return self.place_order(
            quantity=quantity,
            disclosed_quantity=0,
            duration="DAY",
            limit_price=target_price,
            product="MIS",
            instrument=instrument,
            order_type="LIMIT",
            transaction_type=transaction_type,
            trigger_price=0.0,
            trailing_stop_loss=0.0,
            is_amo=False
        )

    def place_stop_loss_order(self, quantity, instrument, stop_loss_price, transaction_type):
        return self.place_order(
            quantity=quantity,
            disclosed_quantity=0,
            duration="DAY",
            limit_price=0.0,
            product="MIS",
            instrument=instrument,
            order_type="SL-M",
            transaction_type=transaction_type,
            trigger_price=stop_loss_price,
            trailing_stop_loss=0.0,
            is_amo=False
        )


# Example usage

    # Place buy order example
    # buy_order_response = client.place_buy_order(
    #     quantity=1,
    #     instrument="NSE_EQ|INE528G01035",
    #     price=500.0
    # )
    # print("Buy Order Response:", buy_order_response)
    #
    # # Place sell order example
    # sell_order_response = client.place_sell_order(
    #     quantity=1,
    #     instrument="NSE_EQ|INE528G01035",
    #     price=550.0
    # )
    # print("Sell Order Response:", sell_order_response)
    #
    # # Place target order example
    # target_order_response = client.place_target_order(
    #     quantity=1,
    #     instrument="NSE_EQ|INE528G01035",
    #     target_price=600.0,
    #     transaction_type="SELL"
    # )
    # print("Target Order Response:", target_order_response)
    #
    # # Place stop loss order example
    # stop_loss_order_response = client.place_stop_loss_order(
    #     quantity=1,
    #     instrument="NSE_EQ|INE528G01035",
    #     stop_loss_price=450.0,
    #     transaction_type="SELL"
    # )
    # print("Stop Loss Order Response:", stop_loss_order_response)

    # Get historical candle data example
    # historical_data_response = client.get_historical_candle_data(
    #     instrument_key='NSE_EQ|INE669E01016',
    #     interval='30minute',
    #     to_date='2023-11-13',
    #     from_date='2023-11-12'
    # )
    # print("Historical Candle Data Response:", historical_data_response)
