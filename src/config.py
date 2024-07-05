import os

from dotenv import load_dotenv

load_dotenv()

KITE_API_SECRET = "04xnxa3qehzacdggw3evgbhxkk8dse5b"
KITE_API_KEY = "ye8rerpg2zxmibju"
PASSPHRASE = "Ivaan@123"
LOGIN_URL = f"https://kite.zerodha.com/connect/login?v=3&api_key=ye8rerpg2zxmibju"
REDIRECT_URL = os.getenv("REDIRECT_URL")
MAX_LOSS = os.getenv("MAX_LOSS", 1000)
