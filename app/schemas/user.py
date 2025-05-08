from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    email: str
    id: int
    username: str
    binance_api_key: str | None = None
    binance_api_secret: str | None = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserStatsOut(BaseModel):
    roi: float
    total_assets: float
    total_loss: float

class BinanceKeys(BaseModel):
    binance_api_key: str
    binance_api_secret: str
