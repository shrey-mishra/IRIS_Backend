from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class WalletHistory(Base):
    __tablename__ = "wallet_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_value_usd = Column(Float)
    snapshot = Column(JSON)  # Optional: dictionary of per-coin balances
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset = Column(String, nullable=False, default="BTC")
    btc_amount = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
