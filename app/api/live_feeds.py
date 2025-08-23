from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from ccxt import binance
import plotly.express as px
import pandas as pd
import json

router = APIRouter()

@router.get("/trending")
def get_trending_coins():
    """Get trending coins with comprehensive market data"""
    try:
        exchange = binance()
        tickers = exchange.fetch_tickers()
        
        trending = []
        for symbol, data in sorted(tickers.items(), key=lambda x: x[1].get("quoteVolume", 0), reverse=True)[:15]:
            # Only include USDT pairs for cleaner data
            if symbol.endswith('/USDT'):
                # Calculate 24h change percentage
                open_24h = data.get("open", 0)
                last_price = data.get("last", 0)
                change_24h = 0
                if open_24h > 0:
                    change_24h = ((last_price - open_24h) / open_24h) * 100
                
                trending.append({
                    "symbol": symbol,
                    "volume": data.get("quoteVolume", 0),
                    "last": last_price,
                    "change_24h": round(change_24h, 2),
                    "high_24h": data.get("high", 0),
                    "low_24h": data.get("low", 0),
                    "bid": data.get("bid", 0),
                    "ask": data.get("ask", 0),
                    "timestamp": data.get("timestamp", 0)
                })
        
        return trending[:10]  # Return top 10 trending coins
        
    except Exception as e:
        # Return fallback data if API fails
        return [
            {
                "symbol": "BTC/USDT",
                "volume": 1000000000,
                "last": 43500,
                "change_24h": 2.5,
                "high_24h": 44000,
                "low_24h": 43000,
                "bid": 43450,
                "ask": 43550,
                "timestamp": pd.Timestamp.now().timestamp() * 1000
            }
        ]

@router.get("/trending-enhanced")
def get_enhanced_trending_coins():
    """Get enhanced trending data with additional market metrics"""
    try:
        exchange = binance()
        tickers = exchange.fetch_tickers()
        
        # Get additional market data
        market_caps = {}
        try:
            # Try to get market cap data from CoinGecko or similar
            # For now, we'll calculate approximate market cap
            for symbol, data in tickers.items():
                if symbol.endswith('/USDT'):
                    volume_24h = data.get("quoteVolume", 0)
                    last_price = data.get("last", 0)
                    # Approximate market cap (this is a simplified calculation)
                    market_caps[symbol] = volume_24h * 0.1  # Rough estimate
        except:
            pass
        
        trending = []
        for symbol, data in sorted(tickers.items(), key=lambda x: x[1].get("quoteVolume", 0), reverse=True)[:20]:
            if symbol.endswith('/USDT'):
                open_24h = data.get("open", 0)
                last_price = data.get("last", 0)
                change_24h = 0
                if open_24h > 0:
                    change_24h = ((last_price - open_24h) / open_24h) * 100
                
                # Calculate additional metrics
                price_change = last_price - open_24h
                volatility = (data.get("high", 0) - data.get("low", 0)) / open_24h * 100 if open_24h > 0 else 0
                
                trending.append({
                    "symbol": symbol,
                    "volume": data.get("quoteVolume", 0),
                    "last": last_price,
                    "change_24h": round(change_24h, 2),
                    "price_change": round(price_change, 2),
                    "high_24h": data.get("high", 0),
                    "low_24h": data.get("low", 0),
                    "bid": data.get("bid", 0),
                    "ask": data.get("ask", 0),
                    "market_cap": market_caps.get(symbol, 0),
                    "volatility": round(volatility, 2),
                    "timestamp": data.get("timestamp", 0)
                })
        
        return trending[:10]
        
    except Exception as e:
        return []

@router.get("/block-orders")
def get_block_orders(symbol: str = "BTC/USDT"):
    exchange = binance()
    trades = exchange.fetch_trades(symbol, limit=100)
    # Filter for large trades (block orders)
    block_orders = [trade for trade in trades if trade["amount"] > 1.0]  # Example threshold
    return block_orders

@router.get("/charts")
def get_live_chart(symbol: str = "BTC/USDT"):
    exchange = binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=60)  # Last 60 minutes
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    fig = px.line(df, x="timestamp", y="close", title=f"Live Chart for {symbol}")
    return json.loads(fig.to_json())