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

