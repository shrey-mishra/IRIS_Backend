# app/utils/binance_utils.py
from ccxt import binance
from app.utils.crypto_utils import decrypt
from app.core.config import settings

def get_authenticated_client(user):
    api_key = decrypt(user.binance_api_key)
    api_secret = decrypt(user.binance_api_secret)
    return binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

def get_wallet_balances(user):
    client = get_authenticated_client(user)
    balances = client.fetch_balance()
    return {k: v for k, v in balances['total'].items() if v > 0}
