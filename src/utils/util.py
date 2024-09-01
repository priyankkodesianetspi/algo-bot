import datetime

import pandas as pd
import pytz


def load_env_vars():
    from dotenv import load_dotenv
    load_dotenv()


def write_order_data_to_file(key, orders):
    df = pd.read_csv('../trades.csv')
    new_rows = [{
        'id': key,
        'order_id': order['order_id'],
        'trading_symbol': order['tradingsymbol'],
        'transaction_type': order['transaction_type'],
        'order_timestamp': order['order_timestamp'],
        'quantity': order['quantity'],
        'status': order['status'],
        'order_type': order['order_type']
    } for order in orders]
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv('trades.csv', index=False, header=True)


def write_missed_order_data_to_file(data, price, stop_loss_price, target_price):
    df = pd.read_csv('../missed_trades.csv')
    new_rows = [{
        'trading_symbol': data['TS'],
        'transaction_type': data['TT'],
        'order_timestamp': datetime.time.time(),
        'price': price,
        'stop_loss': stop_loss_price,
        'target_price': target_price,
    }]
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv('missed_trades.csv', index=False, header=True)


def isTradeTimeAllowed():
    # set the timezone to IST
    tz = pytz.timezone('Asia/Kolkata')

    # get the current time in IST timezone
    now = datetime.datetime.now(tz)
    print(now.time())
    # set the start and end times
    start_time = datetime.time(trade_start_time_h, trade_start_time_m, 0)
    end_time = datetime.time(trade_end_time_h, trade_end_time_m, 0)

    # check if the current time is between the start and end times
    if start_time <= now.time() <= end_time:
        return True
    else:
        return False


def getTotalPNL(positions):
    total_pnl = 0
    for position in positions:
        pnl = (position.sell_value - position.buy_value) + (
                position.quantity * position.last_price * position.multiplier)
        total_pnl += pnl
    return total_pnl


def get_access_token():
    with open('access_token.txt', 'r') as token_file:
        return token_file.read()


def save_to_csv(df, instrument_key):
    # df = clean_and_normalize_data(df)
    file_path = f"data/{instrument_key}.csv"
    df.to_csv(file_path, index=False)
    return file_path


def read_from_csv(instrument_key):
    file_path = f"data/{instrument_key}.csv"
    return pd.read_csv(file_path)


def clean_and_normalize_data(df):
    df = df.dropna()
    # ohlc_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    # ohlc_data = df[ohlc_columns]
    # indicators_data = df.drop(columns=ohlc_columns)
    #
    # scaler = MinMaxScaler()
    # scaled_indicators = scaler.fit_transform(indicators_data)
    # scaled_indicators_df = pd.DataFrame(scaled_indicators, columns=indicators_data.columns, index=indicators_data.index)
    #
    # df = pd.concat([ohlc_data, scaled_indicators_df], axis=1)
    return df


def load_data(file_path):
    df = pd.read_csv(file_path)
    df['Close'] = df['Close'].astype(float)
    return df

# autologin()
# access_token = open("access_token.txt", 'r').read()
# kite.set_access_token(access_token)
# pprint("Kite session generated")

# def autologin():
#     key_secret = open("api_key.txt", 'r').read().split()
#     global kite
#     kite = KiteConnect(api_key=key_secret[0])
#     # service = webdriver.chrome.service.Service('./chromedriver')
#     # pprint(service)
#     # service.start()
#     # options = webdriver.ChromeOptions()
#     # options = options.to_capabilities()
#     # driver = webdriver.Remote(service.service_url, options)
#     driver = webdriver.Chrome('./chromedriver')
#     driver.get(kite.login_url())
#     driver. implicitly_wait (10)
#     username = driver.find_element_by_xpath("//input[@id='userid']")
#     password = driver.find_element_by_xpath("//input[@id='password']")
#     username.send_keys(key_secret[2])
#     password.send_keys(key_secret[3])
#     driver.find_element_by_xpath("//button").click()
#     time.sleep(10)
#     pin = driver.find_element_by_xpath("//label/../input")
#     totp = TOTP(key_secret[4])
#     token = totp.now()
#     print('token', totp, ', ', token)
#     pin.send_keys(token)
#     driver.find_element_by_xpath("//button").click()
#     time.sleep(10)
#     # get the current URL
#     current_url = driver.current_url
#
#     # parse the URL to get the parameter value
#     parsed_url = urllib.parse.urlparse(current_url)
#     query_params = urllib.parse.parse_qs(parsed_url.query)
#     request_token = query_params['request_token'][0]
#     print('request token', request_token)
#     with open("access_token.txt" , "w") as the_file:
#         the_file.write(request_token)
#     driver.quit()
#     request_token = open("access_token.txt" , 'r').read()
#     key_secret = open("api_key.txt", 'r').read().split()
#
#     kite = KiteConnect(api_key=key_secret[0])
#     data = kite.generate_session(request_token, api_secret=key_secret[1])
#     with open('access_token.txt', 'w') as file:
#         file.write(data["access_token"])
#     print("Auto login Completed")
