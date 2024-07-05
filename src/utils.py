import pandas as pd


def load_env_vars():
    from dotenv import load_dotenv
    load_dotenv()


def write_order_data_to_file(key, orders):
    df = pd.read_csv('trades.csv')
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


def get_total_pnl(positions):
    try:
        return sum(pos['pnl'] for pos in positions)
    except Exception:
        return 0


def is_trade_time_allowed():
    # Implement logic to check if the current time is within allowed trading hours
    return True

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
