from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.trade_history import TradeHistory
from app.schemas.trade_history import TradeHistoryOut
from app.core.security import get_current_user
from app.services.auth_service import get_user_by_email
from typing import List

router = APIRouter()

@router.get("/history", response_model=List[TradeHistoryOut])
def get_trade_history(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    trades = db.query(TradeHistory).filter(TradeHistory.user_id == user.id).order_by(TradeHistory.executed_at.desc()).all()
    return trades