
from celery import shared_task
from app.core.database import get_db
from app.models.preferences import Preferences
from app.models.user import User
from app.tasks.trading_tasks import auto_trade_user
from sqlalchemy.orm import Session

@shared_task
def run_auto_trading_all_users():
    db: Session = next(get_db())
    try:
        prefs_with_auto = db.query(Preferences).filter(Preferences.auto_trade == True).all()
        for prefs in prefs_with_auto:
            user = db.query(User).filter(User.id == prefs.user_id).first()
            if user:
                print(f"Running auto-trade for user: {user.email}")
                try:
                    auto_trade_user(email=user.email, db=db)
                except Exception as e:
                    print(f"Failed to auto-trade for {user.email}: {str(e)}")
    finally:
        db.close()
