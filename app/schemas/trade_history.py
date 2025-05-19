from pydantic import BaseModel
from datetime import datetime

class TradeHistoryOut(BaseModel):
    symbol: str
    action: str
    amount: float
    price: float
    executed_at: datetime

    class Config:
        orm_mode = True