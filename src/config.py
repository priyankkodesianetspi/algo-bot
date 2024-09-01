import os

from dotenv import load_dotenv

load_dotenv()

KITE_API_SECRET = "g75rgyq5naf4tkj8lkv5w1i3s9pk70pn"
KITE_API_KEY = "ye8rerpg2zxmibju"
PASSPHRASE = "Ivaan@123"
LOGIN_URL = f"https://kite.zerodha.com/connect/login?v=3&api_key=ye8rerpg2zxmibju"
REDIRECT_URL = "https://13.201.92.141/login"
# REDIRECT_URL="http://127.0.0.1:8000/login"
MAX_LOSS = os.getenv("MAX_LOSS", 1000)
ORDER_TYPE = "LIMIT"
PRODUCT_TYPE = "MIS"
TP = 0.25
SLP = 0.6
