import csv
import logging as logger

from flask import request, jsonify

from kite_service import KiteService
from src.config import PASSPHRASE, MAX_LOSS
from utils import load_env_vars, get_total_pnl

kite_service = KiteService()


def init_routes(app):
    load_env_vars()

    @app.route("/")
    def index():
        return "<a href='/login'><h1>Login</h1></a>"

    @app.route("/trades")
    def get_trades():
        data, orderdata = [], []
        with open('trades.csv', 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                data.append(row['order_id'])

        for i in data:
            orderdata.append(kite_service.kite.order_history(order_id=i))
        return jsonify(orderdata)

    # {"TT":"BUY","TS":"SBIN", "OT":"MARKET", "passphrase": "..."}
    @app.route("/webhook", methods=["POST"])
    def webhook():
        data = request.get_json()
        if data['passphrase'] != PASSPHRASE:
            return "Invalid Passphrase"
        logger.info(f"Received data: {data}")

        kite = kite_service.kite
        if get_total_pnl(kite.positions()) >= int(MAX_LOSS):
            return "PNL exceeded"

        kite_service.place_order(data)
        return "success"

    @app.route("/login")
    def login():
        request_token = request.args.get("request_token")
        if not request_token:
            return "<span style='color: red'>Error while generating request token.</span><a href='/'>Try again.</a>"
        kite_service.generate_kite_session(request_token)
        return "Kite session generated"

    @app.route('/check')
    def heartbeat():
        return "AI server is running", 200
