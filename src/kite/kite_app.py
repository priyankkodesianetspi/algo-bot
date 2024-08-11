import csv
import json
import math
import os
from pprint import pprint
from logzero import logger
import pandas as pd
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

from src._config import *
from src.kite_service import KiteService
from src.utils.util import isTradeTimeAllowed, getTotalPNL

# App
app = Flask(__name__)

# Base settings
PORT = 8000
HOST = "0.0.0.0"
kite_api_secret = "04xnxa3qehzacdggw3evgbhxkk8dse5b"
kite_api_key = "ye8rerpg2zxmibju"
PASSPHRASE = "MayburN!@#1810"

request_token = ""
kite = None
cols = ['order_id', 'tradingsymbol', 'transaction_type', 'order_timestamp', 'quantity', 'status']
df = pd.DataFrame(columns=cols)
df.to_csv('trades.csv', index=False, header=True)

# Create a redirect url
LOGIN_URL = f"https://kite.zerodha.com/connect/login?v=3&api_key=ye8rerpg2zxmibju"
# REDIRECT_URL = "https://13.201.92.141/login"
REDIRECT_URL="https://127.0.0.1:8000/login"

# Templates
index_template = f"""<a href={LOGIN_URL}><h1>Login</h1>"""
login_template = f"<a href={LOGIN_URL}><h1>Login</h1></a>"


def getRequestToken():
    token_file = os.path.join(os.getcwd(), 'access_token.txt')
    with open(token_file, 'r') as f:
        token = f.read()
    return token


@app.route("/")
def index():
    return index_template.format(LOGIN_URL=LOGIN_URL, )


@app.route("/login")
def login():
    global request_token
    request_token = request.args.get("request_token")
    logger.info(f"Request Token: {request_token}")
    if not request_token:
        return """
            <span style="color: red">Error while generating request token.</span><a href='/'>
            Try again.<a>"""
    token_file = os.path.join(os.getcwd(), '../access_token.txt')
    with open(token_file, 'w+') as f:
        f.write(request_token)

    client = KiteService()
    client.generate_kite_session(request_token)
    return kite.profile()


@app.route('/historical-data', methods=['POST'])
def historical_data():
    client = KiteService()
    client.get_historical_data()
    return jsonify({"message": "Dataframe saved to CSV file successfully"}), 200


@app.route("/trades")
def getTrades():
    pprint("Getting Trades")
    data = []
    orderdata = []
    with open('../trades.csv', 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            id = row['order_id']
            data.append(id)

    for i in data:
        orderdata.append(kite.order_history(order_id=i))
    pprint(orderdata)
    return jsonify(orderdata)


# sample input data = [{"TT":"BUY","TS":"AFFLE", "OT":"MARKET"}]
# @app.route("/webhook", methods=["POST"])
# def webhook():
#     data = json.loads(request.data)
#     # if (data['passphrase'] != PASSPHRASE):
#     #   return "Invalid Passphrase"
#     print('received', data[0])
#     if kite is None:
#         generateKiteSession(getRequestToken())
#     if isTradeTimeAllowed() == False:
#         return "invalid time"
#     if getTotalPNL(kite.positions()) >= allowed_pnl:
#         return "PNL exceeded"
#     placeOrder(data[0])
#     return "success"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
