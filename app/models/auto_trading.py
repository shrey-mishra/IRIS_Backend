from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from app.core.database import Base


class AutoTradingSettings(Base):
    __tablename__ = "auto_trading_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    enabled = Column(Boolean, default=False)
    risk_level = Column(Integer, default=3)  # 1..5
    max_trade_size = Column(Float, default=25.0)  # USD cap per trade
    allowed_pairs = Column(String, default="BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,ADA/USDT")
    min_signal_strength = Column(Integer, default=60)  # 0..100 threshold for signals





