from app.utils.binance_utils import get_authenticated_client
from app.services.auth_service import get_user_by_email
from app.utils.crypto_utils import decrypt
from app.core.database import get_db
from app.ml.lstm_model import predict_next_price
from app.models.preferences import Preferences
from fastapi import HTTPException
from sqlalchemy.orm import Session

def auto_trade_user(email: str, symbol: str = "BTC/USDT", amount: float = 0.01, db: Session = next(get_db())):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not prefs or not prefs.auto_trade:
        return {"message": "Auto-trade not enabled for user"}

    try:
        current_price, predicted_price = predict_next_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    diff = (predicted_price - current_price) / current_price
    action = None

    if diff >= prefs.threshold_limit:
        action = "buy"
    elif diff <= -prefs.threshold_limit:
        action = "sell"

    if action:
        try:
            client = get_authenticated_client(user)
            order = client.create_market_order(symbol, action, amount)
            return {"message": f"{action.capitalize()} order executed", "details": order}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Order failed: {str(e)}")
    else:
        return {"message": "No trade triggered by ML prediction"}