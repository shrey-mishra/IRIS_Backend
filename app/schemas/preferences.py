from pydantic import BaseModel

class PreferencesBase(BaseModel):
    auto_trade: bool = False
    threshold_limit: float = 0.02

class PreferencesCreate(PreferencesBase):
    pass

class PreferencesUpdate(PreferencesBase):
    pass

class BinanceKeysUpdate(BaseModel):
    binance_api_key: str = None
    binance_api_secret: str = None

class PreferencesOut(PreferencesBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
