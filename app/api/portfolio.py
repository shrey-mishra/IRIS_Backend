from fastapi import APIRouter, Depends, HTTPException
from app.utils.binance_utils import get_wallet_balances
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioOut
from app.core.security import get_current_user
from app.services.auth_service import get_user_by_email
from app.core.config import settings
from cryptography.fernet import Fernet
from ccxt import binance
from typing import List
import plotly.express as px
import json

router = APIRouter()

@router.post("/add", response_model=PortfolioOut)
def add_portfolio_entry(
    portfolio: PortfolioCreate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_portfolio = Portfolio(
        user_id=user.id,
        btc_amount=portfolio.btc_amount,
        purchase_price=portfolio.purchase_price
    )

    try:
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=List[PortfolioOut])
def get_portfolio(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
    return portfolios

@router.get("/graph")
def get_portfolio_graph(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
    if not portfolios:
        raise HTTPException(status_code=404, detail="No portfolio data found")

    df = [(p.created_at, p.purchase_price) for p in portfolios]
    fig = px.line(x=[x[0] for x in df], y=[x[1] for x in df], title=f"Portfolio for {user.email}")
    return json.loads(fig.to_json())

@router.get("/wallet")
def get_binance_wallet(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        wallet = get_wallet_balances(user)
        return {"wallet": dict(sorted(wallet.items()))}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch wallet data: {str(e)}")
