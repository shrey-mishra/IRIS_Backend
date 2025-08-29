from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # buy/sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    usd_value = Column(Float, nullable=False)
    order_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="completed")
    source = Column(String, nullable=False, default="local")  # local/binance
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)






