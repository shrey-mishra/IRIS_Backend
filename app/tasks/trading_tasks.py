from app.utils.binance_utils import get_authenticated_client
from app.services.auth_service import get_user_by_email
from app.utils.crypto_utils import decrypt
from app.core.database import get_db
from app.models.preferences import Preferences
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.utils.model_utils import get_prediction_from_model
from app.models.trade_history import TradeHistory
from app.utils.notifications_utils import send_telegram_alert, send_email_alert

def auto_trade_user(email: str, symbol: str = "BTC/USDT", amount: float = 0.01, db: Session = next(get_db())):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not prefs or not prefs.auto_trade:
        return {"message": "Auto-trade not enabled for user"}

    try:
        data = get_prediction_from_model(symbol)
        current_price = data["current_price"]
        predicted_high = data["predicted_price_range"]["high"]
        predicted_low = data["predicted_price_range"]["low"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction API failed: {str(e)}")

    diff_up = (predicted_high - current_price) / current_price
    diff_down = (current_price - predicted_low) / current_price

    action = None
    if diff_up >= prefs.threshold_limit:
        action = "buy"
    elif diff_down >= prefs.threshold_limit:
        action = "sell"

    if action:
        try:
            client = get_authenticated_client(user)
            order = client.create_market_order(symbol, action, amount)

            # ✅ Log to DB
            trade = TradeHistory(
                user_id=user.id,
                symbol=symbol,
                action=action,
                amount=amount,
                price=current_price
            )
            db.add(trade)
            db.commit()

            # ✅ Send alert
            msg = (
                f"{action.upper()} ORDER: {symbol} at ${current_price:.2f}\n"
                f"Predicted High: ${predicted_high:.2f}, Predicted Low: ${predicted_low:.2f}"
            )
            send_telegram_alert(msg)
            send_email_alert(
                subject="Trade Executed",
                body=msg,
                to_email=user.email
            )

            return {"message": f"{action.capitalize()} order executed", "details": order}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Order failed: {str(e)}")

    return {"message": "No trade triggered by ML prediction"}
