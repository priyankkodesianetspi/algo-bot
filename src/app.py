import csv
import json
import math
import os
from pprint import pprint

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

# from selenium import webdriver
# from pyotp import TOTP
# import urllib.parse
# import schedule
from utils.util import isTradeTimeAllowed, getTotalPNL, get_access_token

load_dotenv()

# App
app = Flask(__name__)

# Base settings
PORT = 8000
HOST = "127.0.0.1"
kite_api_secret = os.getenv("KITE_API_SECRET", "04xnxa3qehzacdggw3evgbhxkk8dse5b")
kite_api_key = os.getenv("KITE_API_KEY", "ye8rerpg2zxmibju")
login_url = os.getenv("LOGIN_URL")
PASSPHRASE = os.getenv("PASSPHRASE")

allowed_pnl = 1000
trade_start_time_h = 9
trade_start_time_m = 15
trade_end_time_h = 11
trade_end_time_m = 30

request_token = ""
kite = None
cols = ['order_id', 'tradingsymbol', 'transaction_type', 'order_timestamp', 'quantity', 'status']
df = pd.DataFrame(columns=cols)
df.to_csv('trades.csv', index=False, header=True)

# Create a redirect url
redirect_url = f"http://{HOST}:{PORT}/login"

# Templates
index_template = f"""<a href="/index"><h1>Index</h1></a> <a href={login_url}><h1>Login</h1>"""
login_template = f"<a href={login_url}><h1>Login</h1></a>"


@app.route("/index")
def index():
    return index_template.format(login_url=login_url, )


@app.route("/trades")
def getTrades():
    pprint("Getting Trades")
    data = []
    orderdata = []
    with open('trades.csv', 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            id = row['order_id']
            data.append(id)

    for i in data:
        orderdata.append(kite.order_history(order_id=i))
    pprint(orderdata)
    return jsonify(orderdata)


# sample input data = [{"TT":"BUY","TS":"AFFLE", "OT":"MARKET"}]
@app.route("/webhook", methods=["POST"])
def webhook():
    data = json.loads(request.data)
    # if (data['passphrase'] != PASSPHRASE):
    #   return "Invalid Passphrase"
    print('received', data[0])
    if kite is None:
        generateKiteSession(get_access_token())
    if isTradeTimeAllowed() == False:
        return "invalid time"
    if getTotalPNL(kite.positions()) >= allowed_pnl:
        return "PNL exceeded"
    placeOrder(data[0])
    return "success"


def writeOrderDataToFile(orders):
    df = pd.read_csv('trades.csv')
    # Extract the desired columns from the data
    new_rows = []
    for row in orders:
        row = row[0]
        new_row = {'order_id': row['order_id'], 'tradingsymbol': row['tradingsymbol'],
                   'transaction_type': row['transaction_type'], 'order_timestamp': row['order_timestamp'],
                   'quantity': row['quantity'], 'status': row['status'], 'processed': False}
        new_rows.append(new_row)
    # Append the new rows to the existing DataFrame
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    # Write the updated DataFrame to the file
    df.to_csv('trades.csv', index=False, header=True)


@app.route("/login")
def login():
    global request_token
    request_token = request.args.get("request_token")
    if not request_token:
        return """
            <span style="color: red">Error while generating request token.</span><a href='/'>
            Try again.<a>"""
    token_file = os.path.join(os.getcwd(), 'access_token.txt')
    with open(token_file, 'w+') as f:
        f.write(request_token)
    generateKiteSession(request_token)
    return kite.profile()


def getQuantity(bal, price):
    # considering the margin(5X) and some buffer
    quantity = math.floor((bal * 4.99) / price)
    return 100


def generateKiteSession(request_token):
    print("Generating Kite Session with request token: " + request_token)
    global kite
    kite = KiteConnect(api_key=kite_api_key)
    data = kite.generate_session(request_token, api_secret=kite_api_secret)
    kite.set_access_token(data["access_token"])


def getStockLTP(symbol):
    instrument = f'NSE:{symbol}'
    return kite.quote(instrument)[instrument]['last_price']


def getCurrentBalance():
    return kite.margins()['equity']['available']['cash']

def createPrimaryOrder(symbol, quantity, price, transaction_type, order_type):
    if (order_type == 'LIMIT'):
        order_id = createLimitOrder(symbol, quantity, price, transaction_type, order_type)
    else:
        order_id = kite.place_order(tradingsymbol=symbol, exchange=kite.EXCHANGE_NSE, transaction_type=transaction_type,
                                    quantity=quantity, variety=kite.VARIETY_REGULAR, order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_MIS, validity=kite.VALIDITY_DAY)
    return order_id


def createLimitOrder(symbol, quantity, price, transaction_type, order_type):
    order_id = kite.place_order(tradingsymbol=symbol, exchange=kite.EXCHANGE_NSE, transaction_type=transaction_type,
                                quantity=quantity, price=price, variety=kite.VARIETY_REGULAR, order_type=order_type,
                                product=kite.PRODUCT_MIS, validity=kite.VALIDITY_DAY)
    return order_id


def createSLOrder(symbol, quantity, price, transaction_type, order_type):
    order_id = kite.place_order(tradingsymbol=symbol, exchange=kite.EXCHANGE_NSE, transaction_type=transaction_type,
                                quantity=quantity, trigger_price=price, variety=kite.VARIETY_REGULAR,
                                order_type=order_type, product=kite.PRODUCT_MIS, validity=kite.VALIDITY_DAY)
    return order_id


def placeOrder(data):
    if (kite is None):
        return "Kite session not generated"
    print(data)
    symbol = data['TS']
    bal = getCurrentBalance()
    price = getStockLTP(symbol)
    targetPrice = round((price * 1.0020) * 20) / 20
    stopLossPrice = round(((price * 0.99) * 1.0020) * 20) / 20

    quantity = getQuantity(bal, price)

    if quantity == 0:
        return "Not enough balance to place order"

    primary_transaction_type = 'SELL' if data['TT'] == 'SELL' else 'BUY'
    primary_order_type = 'LIMIT' if data['OT'] == 'LIMIT' else 'MARKET'

    target_transaction_type = 'BUY' if primary_transaction_type == 'SELL' else 'SELL'
    target_order_type = 'LIMIT'

    stop_loss_transaction_type = 'BUY' if primary_transaction_type == 'SELL' else 'SELL'
    stop_loss_order_type = 'SL-M'

    pprint(f"Placing order : "
           f"Cash Balance {bal}, "
           f"Stock {symbol}, "
           f"Last Traded Price: {price}, "
           f"Quantity: {quantity}")

    # primary order
    primaryOrderId = createPrimaryOrder(symbol, quantity, price, primary_transaction_type, primary_order_type)

    # target order
    targetOrderId = createLimitOrder(symbol, quantity, targetPrice, target_transaction_type, target_order_type)

    # stoploss order
    slOrderId = createSLOrder(symbol, quantity, stopLossPrice, stop_loss_transaction_type, stop_loss_order_type)

    primaryOrder = kite.order_history(order_id=primaryOrderId)
    targetOrder = kite.order_history(order_id=targetOrderId)
    slOrder = kite.order_history(order_id=slOrderId)
    writeOrderDataToFile([primaryOrder])



@app.route('/check')
def heartbeat():
    return "AI server is running", 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)
