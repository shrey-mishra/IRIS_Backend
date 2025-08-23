from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_email
from app.core.security import get_current_user
from app.core.config import settings
from app.ml.lstm_model import predict_next_price
from ccxt import binance
import json
from cryptography.fernet import Fernet
import requests
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

cipher = Fernet(settings.FERNET_KEY.encode())

# In-memory storage for recent trades (in production, use database)
recent_trades: Dict[str, List[Dict[str, Any]]] = {}

# Pydantic models for request validation
class DirectTradeRequest(BaseModel):
    symbol: str = "BTC/USDT"
    side: str = "buy"
    usd_amount: float = 10.0
    stop_loss: float = None

class DirectTradeResponse(BaseModel):
    message: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usd_amount: float
    status: str
    timestamp: str
    details: Dict[str, Any]

def store_trade_record(user_email: str, trade_data: Dict[str, Any]):
    """Store trade record for recent transactions display"""
    try:
        if user_email not in recent_trades:
            recent_trades[user_email] = []
        
        trade_record = {
            "id": str(uuid.uuid4()),
            "type": trade_data["side"],
            "symbol": trade_data["symbol"],
            "amount": trade_data["quantity"],
            "price": trade_data["price"],
            "usd_value": trade_data["usd_amount"],
            "timestamp": datetime.now().timestamp() * 1000,  # Convert to milliseconds
            "status": "completed",
            "fee": {"cost": 0, "currency": "USDT"},
            "order_id": trade_data["order_id"],
            "source": "local"
        }
        
        # Add to beginning of list (most recent first)
        recent_trades[user_email].insert(0, trade_record)
        
        # Keep only last 50 trades
        if len(recent_trades[user_email]) > 50:
            recent_trades[user_email] = recent_trades[user_email][:50]
        
        print(f"DEBUG: Successfully stored trade record for {user_email}: {trade_record}")
        print(f"DEBUG: Total local trades for {user_email}: {len(recent_trades[user_email])}")
        return trade_record
        
    except Exception as e:
        print(f"DEBUG: Error storing trade record: {e}")
        return None

def refresh_binance_token(user: User, db: Session):
    token_url = "https://accounts.binance.com/en/oauth/token"
    data = {
        "client_id": settings.BINANCE_CLIENT_ID,
        "client_secret": settings.BINANCE_CLIENT_SECRET,
        "refresh_token": cipher.decrypt(user.binance_api_secret.encode()).decode(),
        "grant_type": "refresh_token"
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        user.binance_api_key = cipher.encrypt(token_data["access_token"].encode()).decode()
        user.binance_api_secret = cipher.encrypt(token_data["refresh_token"].encode()).decode()
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Failed to refresh Binance token")

def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical indicators for market analysis"""
    try:
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        # Moving Averages
        ma_20 = df['close'].rolling(window=20).mean()
        ma_50 = df['close'].rolling(window=50).mean()
        
        return {
            'rsi': rsi.iloc[-1] if not rsi.empty else 50,
            'macd': macd.iloc[-1] if not macd.empty else 0,
            'macd_signal': signal.iloc[-1] if not signal.empty else 0,
            'bb_upper': upper_band.iloc[-1] if not upper_band.empty else 0,
            'bb_lower': lower_band.iloc[-1] if not lower_band.empty else 0,
            'ma_20': ma_20.iloc[-1] if not ma_20.empty else 0,
            'ma_50': ma_50.iloc[-1] if not ma_50.empty else 0,
            'current_price': df['close'].iloc[-1] if not df.empty else 0
        }
    except Exception as e:
        return {}

def generate_market_signal(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """Generate market signal based on technical indicators"""
    try:
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        current_price = indicators.get('current_price', 0)
        ma_20 = indicators.get('ma_20', 0)
        ma_50 = indicators.get('ma_50', 0)
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        # Calculate signal strength and factors
        factors = []
        strength = 0
        
        # RSI analysis
        if rsi < 30:
            factors.append("RSI oversold")
            strength += 20
        elif rsi > 70:
            factors.append("RSI overbought")
            strength -= 20
        
        # MACD analysis
        if macd > macd_signal:
            factors.append("MACD bullish crossover")
            strength += 15
        else:
            factors.append("MACD bearish crossover")
            strength -= 15
        
        # Moving average analysis
        if current_price > ma_20 > ma_50:
            factors.append("Price above moving averages")
            strength += 15
        elif current_price < ma_20 < ma_50:
            factors.append("Price below moving averages")
            strength -= 15
        
        # Bollinger Bands analysis
        if current_price < bb_lower:
            factors.append("Price below lower Bollinger Band")
            strength += 10
        elif current_price > bb_upper:
            factors.append("Price above upper Bollinger Band")
            strength -= 10
        
        # Determine signal type
        if strength >= 40:
            signal = "STRONG_BUY"
        elif strength >= 20:
            signal = "BUY"
        elif strength <= -40:
            signal = "STRONG_SELL"
        elif strength <= -20:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            "signal": signal,
            "strength": min(100, max(0, abs(strength))),
            "factors": factors,
            "indicators": indicators
        }
    except Exception as e:
        return {
            "signal": "NEUTRAL",
            "strength": 50,
            "factors": ["Analysis unavailable"],
            "indicators": {}
        }

@router.get("/market-signals")
def get_market_signals(symbol: str = "BTC/USDT", current_user_email: str = Depends(get_current_user)):
    """Get market signals based on technical analysis"""
    try:
        exchange = binance()
        
        # Fetch historical data for technical analysis
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1h", limit=100)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # Calculate technical indicators
        indicators = calculate_technical_indicators(df)
        
        # Generate market signal
        signal_data = generate_market_signal(indicators)
        
        return {
            "symbol": symbol,
            "signal": signal_data["signal"],
            "strength": signal_data["strength"],
            "factors": signal_data["factors"],
            "indicators": signal_data["indicators"],
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate market signals: {str(e)}")

@router.get("/market-signals-all")
def get_all_market_signals(current_user_email: str = Depends(get_current_user)):
    """Get market signals for all supported symbols"""
    try:
        supported_symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
        all_signals = []
        
        for symbol in supported_symbols:
            try:
                signal = get_market_signals(symbol, current_user_email)
                all_signals.append(signal)
            except Exception as e:
                # If one symbol fails, add a fallback signal
                all_signals.append({
                    "symbol": symbol,
                    "signal": "NEUTRAL",
                    "strength": 50,
                    "factors": [f"Data unavailable: {str(e)}"],
                    "indicators": {},
                    "timestamp": pd.Timestamp.now().isoformat()
                })
        
        return all_signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate all market signals: {str(e)}")

@router.get("/ai-performance")
def get_ai_performance(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get AI trading performance metrics"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # This would typically come from a database table tracking AI trades
        # For now, return mock data structure
        return {
            "total_trades": 0,
            "success_rate": 0.0,
            "total_profit": 0.0,
            "avg_confidence": 0.0,
            "active_time": "0h 0m"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI performance: {str(e)}")

@router.post("/ai-auto-trade")
def execute_ai_auto_trade(
    symbol: str = "BTC/USDT",
    risk_level: int = 3,
    max_trade_size: float = 25.0,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute AI-powered automated trade"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get market signal
        signal_response = get_market_signals(symbol, current_user_email)
        signal = signal_response["signal"]
        strength = signal_response["strength"]
        
        # Check if signal is strong enough for trading
        if signal in ["NEUTRAL"] or strength < 60:
            return {
                "message": "No trade executed - insufficient signal strength",
                "signal": signal,
                "strength": strength,
                "reason": "Market conditions not favorable"
            }
        
        # Calculate trade size based on risk level
        base_trade_size = 0.01  # Minimum trade size
        risk_multiplier = risk_level / 5.0
        trade_size = base_trade_size * risk_multiplier * (max_trade_size / 100.0)
        
        # Determine trade side based on signal
        if signal in ["STRONG_BUY", "BUY"]:
            side = "buy"
        else:
            side = "sell"
        
        # Execute the trade
        trade_result = execute_trade(
            symbol=symbol,
            side=side,
            amount=trade_size,
            current_user_email=current_user_email,
            db=db
        )
        
        return {
            "message": "AI auto trade executed successfully",
            "trade_details": trade_result,
            "signal": signal,
            "strength": strength,
            "trade_size": trade_size,
            "risk_level": risk_level
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI auto trade failed: {str(e)}")

@router.post("/execute")
def execute_trade(
    symbol: str = "BTC/USDT",
    side: str = "buy",
    amount: float = 0.01,
    stop_loss: float = None,  # Optional stop-loss price
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.binance_api_key or not user.binance_api_secret:
        raise HTTPException(status_code=400, detail="Binance API credentials not provided")

    api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
    api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

    exchange = binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    # Predict next price using LSTM
    try:
        current_price, predicted_price = predict_next_price(symbol)
        print(f"DEBUG: Current price: {current_price}, Predicted price: {predicted_price}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price prediction failed: {str(e)}")

    # Decide whether to trade based on prediction
    if side == "buy" and predicted_price > current_price:
        print("DEBUG: Predicted price increase - proceeding with buy")
    elif side == "sell" and predicted_price < current_price:
        print("DEBUG: Predicted price decrease - proceeding with sell")
    else:
        print("DEBUG: No trade - prediction does not favor the action")
        return {"message": "No trade executed - prediction does not favor the action"}

    try:
        # Execute market order
        order = exchange.create_market_order(symbol, side, amount)
        
        # If stop-loss is provided, create a stop-loss order
        if stop_loss:
            stop_side = "sell" if side == "buy" else "buy"
            exchange.create_order(symbol, "stop_loss_limit", stop_side, amount, stop_loss, {"stopPrice": stop_loss})
            print(f"DEBUG: Stop-loss order placed at {stop_loss}")

        return {"message": f"Trade executed: {json.dumps(order)}"}
    except Exception as e:
        if "invalid api key" in str(e).lower() or "permission" in str(e).lower():
            refresh_binance_token(user, db)
            api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
            api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()
            exchange = binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            order = exchange.create_market_order(symbol, side, amount)
            if stop_loss:
                stop_side = "sell" if side == "buy" else "buy"
                exchange.create_order(symbol, "stop_loss_limit", stop_side, amount, stop_loss, {"stopPrice": stop_loss})
            return {"message": f"Trade executed after refresh: {json.dumps(order)}"}
        raise HTTPException(status_code=500, detail=f"Trade failed: {str(e)}")

@router.post("/execute-direct", response_model=DirectTradeResponse)
def execute_direct_trade(
    trade_request: DirectTradeRequest,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute trade directly without LSTM prediction - for immediate trading"""
    try:
        # Extract data from request model
        symbol = trade_request.symbol
        side = trade_request.side
        usd_amount = trade_request.usd_amount
        stop_loss = trade_request.stop_loss
        
        # Debug logging
        print(f"DEBUG: Received trade request - Symbol: {symbol}, Side: {side}, USD Amount: {usd_amount}")
        
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.binance_api_key or not user.binance_api_secret:
            raise HTTPException(status_code=400, detail="Binance API credentials not provided")

        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Get current price to calculate quantity
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Calculate quantity based on USD amount
        quantity = usd_amount / current_price
        
        # Ensure minimum quantity (Binance requirements)
        min_quantity = 0.0001  # Minimum for most pairs
        if quantity < min_quantity:
            min_usd_value = min_quantity * current_price
            raise HTTPException(
                status_code=400, 
                detail=f"Amount too small. Minimum trade value for {symbol}: ${min_usd_value:.2f}. You entered: ${usd_amount:.2f}"
            )

        print(f"DEBUG: Executing {side} order for {quantity:.6f} {symbol} at ~${current_price:.2f} (${usd_amount:.2f})")

        # Check balance before executing trade
        try:
            balance = exchange.fetch_balance()
            if side == "buy":
                # For buying, check USDT balance
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                if usdt_balance < usd_amount:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient USDT balance. You have ${usdt_balance:.2f} USDT, but need ${usd_amount:.2f} USDT to buy {symbol}"
                    )
            elif side == "sell":
                # For selling, check crypto balance
                crypto_symbol = symbol.split('/')[0]  # Get ETH from ETH/USDT
                crypto_balance = balance.get(crypto_symbol, {}).get('free', 0)
                crypto_value = crypto_balance * current_price
                if crypto_value < usd_amount:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient {crypto_symbol} balance. You have ${crypto_value:.2f} worth of {crypto_symbol}, but trying to sell ${usd_amount:.2f} worth"
                    )
        except Exception as balance_error:
            print(f"DEBUG: Balance check failed: {balance_error}")
            # Continue with trade execution if balance check fails

        # Execute market order
        order = exchange.create_market_order(symbol, side, quantity)
        
        # If stop-loss is provided, create a stop-loss order
        if stop_loss:
            stop_side = "sell" if side == "buy" else "buy"
            try:
                exchange.create_order(symbol, "stop_loss_limit", stop_side, quantity, stop_loss, {"stopPrice": stop_loss})
                print(f"DEBUG: Stop-loss order placed at {stop_loss}")
            except Exception as sl_error:
                print(f"DEBUG: Stop-loss order failed: {sl_error}")

        # Get updated order details
        order_details = exchange.fetch_order(order['id'], symbol)
        
        trade_data_to_store = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": current_price,
            "usd_amount": usd_amount,
            "order_id": order['id']
        }
        store_trade_record(current_user_email, trade_data_to_store)

        return DirectTradeResponse(
            message=f"Trade executed successfully!",
            order_id=order['id'],
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            usd_amount=usd_amount,
            status=order_details.get('status', 'unknown'),
            timestamp=str(order_details.get('timestamp', '')),
            details=order_details
        )
        
    except Exception as e:
        print(f"DEBUG: Trade execution failed: {str(e)}")
        if "insufficient balance" in str(e).lower():
            raise HTTPException(status_code=400, detail="Insufficient balance for this trade")
        elif "invalid api key" in str(e).lower() or "permission" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid API credentials or insufficient permissions")
        elif "amount too small" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Trade failed: {str(e)}")

@router.get("/wallet-balance")
def get_wallet_balance(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get real-time Binance wallet balance and account information"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.binance_api_key or not user.binance_api_secret:
            raise HTTPException(status_code=400, detail="Binance API credentials not provided")

        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Get account information
        account_info = exchange.fetch_balance()
        
        # Get current prices for major cryptocurrencies
        tickers = exchange.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT'])
        
        # Calculate total USD value
        total_usd_value = 0
        crypto_balances = []
        
        for currency, balance in account_info['total'].items():
            if balance > 0:
                if currency == 'USDT':
                    total_usd_value += balance
                    crypto_balances.append({
                        'currency': currency,
                        'balance': balance,
                        'usd_value': balance,
                        'price_usd': 1.0
                    })
                else:
                    # Find USDT pair for this currency
                    usdt_pair = f"{currency}/USDT"
                    if usdt_pair in tickers:
                        price_usd = tickers[usdt_pair]['last']
                        usd_value = balance * price_usd
                        total_usd_value += usd_value
                        crypto_balances.append({
                            'currency': currency,
                            'balance': balance,
                            'usd_value': usd_value,
                            'price_usd': price_usd
                        })
                    else:
                        # If no USDT pair, just show the balance
                        crypto_balances.append({
                            'currency': currency,
                            'balance': balance,
                            'usd_value': 0,
                            'price_usd': 0
                        })

        # Sort by USD value (highest first)
        crypto_balances.sort(key=lambda x: x['usd_value'], reverse=True)

        return {
            "total_usd_value": total_usd_value,
            "crypto_balances": crypto_balances,
            "account_status": "connected",
            "last_updated": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        if "invalid api key" in str(e).lower() or "permission" in str(e).lower():
            return {
                "total_usd_value": 0,
                "crypto_balances": [],
                "account_status": "invalid_credentials",
                "error": "Invalid Binance API credentials"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to fetch wallet balance: {str(e)}")

@router.get("/wallet-status")
def get_wallet_status(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check if user's Binance wallet is connected and valid"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.binance_api_key or not user.binance_api_secret:
            return {
                "connected": False,
                "status": "no_credentials",
                "message": "No Binance API credentials found"
            }

        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Test connection by getting account info
        account_info = exchange.fetch_balance()
        
        return {
            "connected": True,
            "status": "connected",
            "message": "Wallet connected successfully",
            "account_type": "spot",
            "last_updated": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "message": f"Connection failed: {str(e)}"
        }

@router.get("/transactions")
def get_user_transactions(
    limit: int = 20,
    current_user_email: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get user's recent trading transactions from both local records and Binance"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get local trade records first
        local_trades = recent_trades.get(current_user_email, [])
        print(f"DEBUG: Found {len(local_trades)} local trades for {current_user_email}")
        
        # Try to get Binance trades if API credentials are available
        binance_trades = []
        if user.binance_api_key and user.binance_api_secret:
            try:
                api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
                api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()
                
                exchange = binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                })
                
                # Get recent trades from Binance
                binance_trades_raw = exchange.fetch_my_trades(limit=limit)
                
                if binance_trades_raw and isinstance(binance_trades_raw, list):
                    for trade in binance_trades_raw:
                        if trade and isinstance(trade, dict):
                            try:
                                usd_value = trade.get("amount", 0) * trade.get("price", 0)
                                binance_trades.append({
                                    "id": trade.get("id", ""),
                                    "type": "buy" if trade.get("side") == "buy" else "sell",
                                    "symbol": trade.get("symbol", ""),
                                    "amount": trade.get("amount", 0),
                                    "price": trade.get("price", 0),
                                    "usd_value": usd_value,
                                    "timestamp": trade.get("timestamp", 0),
                                    "status": "completed",
                                    "fee": trade.get("fee", {"cost": 0, "currency": "USDT"}),
                                    "order_id": trade.get("order", ""),
                                    "source": "binance"
                                })
                            except Exception as trade_error:
                                print(f"DEBUG: Error processing individual trade: {trade_error}")
                                continue
                else:
                    print(f"DEBUG: Binance trades response is not a list: {type(binance_trades_raw)}")
                
                print(f"DEBUG: Found {len(binance_trades)} valid Binance trades")
                
            except Exception as binance_error:
                print(f"DEBUG: Failed to fetch Binance trades: {binance_error}")
                # Continue with local trades only
        
        # Combine local and Binance trades
        all_trades = local_trades + binance_trades
        
        # Sort by timestamp (newest first)
        all_trades.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Return combined trades up to the limit
        return all_trades[:limit]
        
    except Exception as e:
        print(f"DEBUG: Error in get_user_transactions: {e}")
        # Return local trades only if there's an error
        return recent_trades.get(current_user_email, [])

@router.get("/debug/trades")
def debug_trades(current_user_email: str = Depends(get_current_user)):
    """Debug endpoint to view stored trade records"""
    local_trades = recent_trades.get(current_user_email, [])
    return {
        "user_email": current_user_email,
        "local_trades_count": len(local_trades),
        "local_trades": local_trades,
        "all_users_trades": {email: len(trades) for email, trades in recent_trades.items()}
    }

@router.post("/debug/add-test-trade")
def add_test_trade(current_user_email: str = Depends(get_current_user)):
    """Add a test trade record for debugging"""
    test_trade_data = {
        "symbol": "ETH/USDT",
        "side": "sell",
        "quantity": 0.004258,
        "price": 4697.50,
        "usd_amount": 20.0,
        "order_id": "test_order_123"
    }
    
    result = store_trade_record(current_user_email, test_trade_data)
    
    return {
        "message": "Test trade added",
        "result": result,
        "total_trades": len(recent_trades.get(current_user_email, []))
    }

@router.get("/transaction-summary")
def get_transaction_summary(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get summary statistics of user's trading activity"""
    try:
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.binance_api_key or not user.binance_api_secret:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "favorite_pairs": [],
                "last_trade_date": None
            }
        
        # Get transactions first
        transactions = get_user_transactions(100, current_user_email, db)
        
        if not transactions:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "favorite_pairs": [],
                "last_trade_date": None
            }
        
        # Calculate summary statistics
        total_trades = len(transactions)
        total_volume = sum(t["usd_value"] for t in transactions)
        successful_trades = len([t for t in transactions if t["status"] == "completed"])
        failed_trades = total_trades - successful_trades
        
        # Get favorite trading pairs
        pair_counts = {}
        for t in transactions:
            pair = t["symbol"]
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
        
        favorite_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        favorite_pairs = [{"symbol": pair, "count": count} for pair, count in favorite_pairs]
        
        # Get last trade date
        last_trade_date = None
        if transactions:
            last_trade_date = pd.Timestamp(transactions[0]["timestamp"], unit="ms").isoformat()
        
        return {
            "total_trades": total_trades,
            "total_volume": round(total_volume, 2),
            "successful_trades": successful_trades,
            "failed_trades": failed_trades,
            "favorite_pairs": favorite_pairs,
            "last_trade_date": last_trade_date
        }
        
    except Exception as e:
        return {
            "total_trades": 0,
            "total_volume": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "favorite_pairs": [],
            "last_trade_date": None
        }