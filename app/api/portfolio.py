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
from app.models.trade_history import TradeHistory

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
        asset=portfolio.asset,
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

@router.get("/summary")
def get_portfolio_summary(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    portfolio_entries = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()

    # Fetch Binance API keys from user preferences (replace with your actual logic)
    api_key = user.preferences.binance_api_key if user.preferences else None
    api_secret = user.preferences.binance_api_secret if user.preferences else None

    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Binance API keys not found for user")

    exchange = binance({
        'apiKey': api_key,
        'secret': api_secret,
    })

    try:
        balances = exchange.fetch_balance()
        #print(balances)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch balances from Binance: {str(e)}")

    #Coin name mapping
    symbol_to_name = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "LTC": "Litecoin",
        "BNB": "Binance Coin",
        "XRP": "Ripple",
    }

    # Structure to hold results
    portfolio_summary = []
    total_value_usd = 0
    overall_gain_loss = 0

    for entry in portfolio_entries:
        symbol = entry.asset  # Get symbol from the portfolio entry
        amount = entry.btc_amount
        purchase_price = entry.purchase_price

        # Fetch current price
        try:
            ticker = exchange.fetch_ticker(f"{symbol}/USDT")
            current_price = ticker['last']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not fetch ticker for {symbol}: {str(e)}")

        # Calculate gain/loss %
        gain_loss_percentage = (current_price - purchase_price) / purchase_price * 100

        # Calculate current value in USD
        current_value_usd = current_price * amount

        # Update totals
        total_value_usd += current_value_usd
        overall_gain_loss += (current_price - purchase_price) * amount

        # Format the result
        portfolio_summary.append({
            "coin": symbol_to_name.get(symbol, symbol),
            "amount": amount,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "gain_loss_percentage": gain_loss_percentage,
            "current_value_usd": current_value_usd
        })

    overall_gain_loss_percentage = (overall_gain_loss / total_value_usd) * 100 if total_value_usd else 0

    return {
        "portfolio_summary": portfolio_summary,
        "total_value_usd": total_value_usd,
        "overall_gain_loss_percentage": overall_gain_loss_percentage
    }

@router.get("/timeseries")
def get_portfolio_timeseries(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch trade history and portfolio data
    trade_history = db.query(TradeHistory).filter(TradeHistory.user_id == user.id).all()
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()

    # Aggregate trades by date
    trades_by_date = {}
    for trade in trade_history:
        date = trade.executed_at.strftime("%d/%m")
        if date not in trades_by_date:
            trades_by_date[date] = []
        trades_by_date[date].append(trade)

    # Calculate gain/loss and total value for each date
    timeseries_data = []
    for date, trades in trades_by_date.items():
        gain = 0
        loss = 0
        amt = 0
        for trade in trades:
            # Get average purchase price from portfolio
            asset_portfolio = next((p for p in portfolio if p.asset == trade.symbol), None)
            if asset_portfolio:
                purchase_price = asset_portfolio.purchase_price
            else:
                purchase_price = 0  # Handle case where asset is not in portfolio

            # Calculate gain/loss
            if trade.price > purchase_price:
                gain += trade.amount * (trade.price - purchase_price)
            elif trade.price < purchase_price:
                loss += trade.amount * (purchase_price - trade.price)

            # Calculate total value
            amt += trade.amount * trade.price

        timeseries_data.append({
            "name": date,
            "Gain": gain,
            "Loss": loss,
            "amt": amt
        })

    return timeseries_data
