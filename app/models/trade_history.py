from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    action = Column(String)  # 'buy' or 'sell'
    amount = Column(Float)
    price = Column(Float)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())