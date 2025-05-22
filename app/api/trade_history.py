from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.models.trade_history import TradeHistory
from datetime import datetime

router = APIRouter()

@router.get("/history")
async def get_trade_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    symbol: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None)
):
    query = db.query(TradeHistory).filter(TradeHistory.user_id == current_user.id)

    if symbol:
        query = query.filter(TradeHistory.symbol == symbol)
    if from_date:
        query = query.filter(TradeHistory.executed_at >= from_date)
    if to_date:
        query = query.filter(TradeHistory.executed_at <= to_date)

    trades = query.order_by(TradeHistory.executed_at.desc()).all()

    return [
        {
            "symbol": trade.symbol,
            "action": trade.action,
            "amount": trade.amount,
            "price": trade.price,
            "executed_at": trade.executed_at.isoformat()
        }
        for trade in trades
    ]
