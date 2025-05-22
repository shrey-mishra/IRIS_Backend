from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.portfolio import WalletHistory
from app.core.config import settings
from cryptography.fernet import Fernet
cipher = Fernet(settings.FERNET_KEY.encode())
from ccxt import binance
from datetime import datetime

@shared_task
def record_wallet_history(user_email: str):
    db: Session = get_db()
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        print(f"User not found: {user_email}")
        return

    if not user.binance_api_key or not user.binance_api_secret:
        print(f"Binance API credentials not provided for user: {user_email}")
        return

    try:
        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        balances = exchange.fetch_balance()
        total_value_usd = 0
        snapshot = {}

        for coin, balance in balances['total'].items():
            if coin == 'USDT':
                total_value_usd += balance
                snapshot[coin] = balance
            elif balance > 0:
                try:
                    ticker = exchange.fetch_ticker(f"{coin}/USDT")
                    price = ticker['last']
                    usd_value = balance * price
                    total_value_usd += usd_value
                    snapshot[coin] = balance
                except Exception as e:
                    print(f"Error fetching price for {coin}: {e}")

        wallet_history = WalletHistory(
            user_id=user.id,
            total_value_usd=total_value_usd,
            snapshot=snapshot,
            recorded_at=datetime.utcnow()
        )

        db.add(wallet_history)
        db.commit()
        print(f"Wallet history recorded for user: {user_email}")

    except Exception as e:
        print(f"Error recording wallet history for user {user_email}: {e}")
    finally:
        db.close()
