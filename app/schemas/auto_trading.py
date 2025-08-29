from pydantic import BaseModel, Field
from typing import List


class AutoTradingSettingsBase(BaseModel):
    enabled: bool = False
    risk_level: int = Field(ge=1, le=5, default=3)
    max_trade_size: float = 25.0
    pairs: List[str] = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
    min_signal_strength: int = Field(ge=0, le=100, default=60)


class AutoTradingSettingsUpdate(AutoTradingSettingsBase):
    pass


class AutoTradingSettingsOut(AutoTradingSettingsBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True





