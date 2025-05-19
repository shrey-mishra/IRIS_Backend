from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.tasks.trading_tasks import auto_trade_user
from app.core.security import get_current_user
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/auto-run")
def manual_auto_trade(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return auto_trade_user(email=current_user_email, db=db)

@router.get("/force-auto-run")
def force_run_scheduler():
    from app.tasks.scheduler import run_auto_trading_all_users
    run_auto_trading_all_users.delay()
    return {"status": "Triggered manually"}

