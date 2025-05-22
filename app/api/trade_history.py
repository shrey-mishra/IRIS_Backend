from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.models.trade_history import TradeHistory
from datetime import datetime, timedelta

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

@router.get("/live")
async def get_live_trade(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    threshold = now - timedelta(seconds=60)

    trade = (
        db.query(TradeHistory)
        .filter(TradeHistory.user_id == current_user.id)
        .filter(TradeHistory.executed_at >= threshold)
        .order_by(TradeHistory.executed_at.desc())
        .first()
    )

    if trade:
        return {
            "is_live": True,
            "symbol": trade.symbol,
            "action": trade.action,
            "amount": trade.amount,
            "executed_price": trade.price,
            "executed_at": trade.executed_at.isoformat()
        }
    else:
        return {"is_live": False}

@router.get("/trades/placed")
async def get_user_trades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None)
):
    trades = (
        db.query(TradeHistory)
        .filter(TradeHistory.user_id == current_user.id)
        .order_by(TradeHistory.executed_at.desc())
    )

    if limit:
        trades = trades.limit(limit)

    trades = trades.all()

    return [
        {
            "symbol": trade.symbol.split("/")[0],
            "executed_price": f"${trade.price:.2f}",
            "commodity_received": f"{trade.amount:.8f}",
            "executed_at": trade.executed_at.strftime("%d %b %I:%M %p")
        }
        for trade in trades
    ]
