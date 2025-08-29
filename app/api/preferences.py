from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.preferences import Preferences
from app.schemas.preferences import PreferencesCreate, PreferencesUpdate, PreferencesOut, BinanceKeysUpdate
from app.core.security import get_current_user
from app.services.auth_service import get_user_by_email, update_binance_keys, validate_binance_keys
from app.models.auto_trading import AutoTradingSettings
from app.schemas.auto_trading import AutoTradingSettingsUpdate, AutoTradingSettingsOut

router = APIRouter()

@router.put("/binance_keys", response_model=None)
def update_binance_keys_route(
    binance_keys: BinanceKeysUpdate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not validate_binance_keys(binance_keys.binance_api_key, binance_keys.binance_api_secret):
        raise HTTPException(status_code=400, detail="Invalid Binance keys")

    update_binance_keys(db, user, binance_keys.binance_api_key, binance_keys.binance_api_secret)
    return {"message": "Binance keys updated successfully"}


@router.post("/", response_model=PreferencesOut)
def create_preferences(
    preferences: PreferencesCreate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_prefs = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if existing_prefs:
        raise HTTPException(status_code=400, detail="Preferences already exist for this user")

    db_preferences = Preferences(
        user_id=user.id,
        auto_trade=preferences.auto_trade,
        threshold_limit=preferences.threshold_limit
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


# --- Auto Trading Settings Endpoints ---

@router.get("/auto-trading", response_model=AutoTradingSettingsOut)
def get_auto_trading_settings(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.query(AutoTradingSettings).filter(AutoTradingSettings.user_id == user.id).first()
    if not settings:
        # Initialize default settings for user
        settings = AutoTradingSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/auto-trading", response_model=AutoTradingSettingsOut)
def update_auto_trading_settings(
    payload: AutoTradingSettingsUpdate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.query(AutoTradingSettings).filter(AutoTradingSettings.user_id == user.id).first()
    if not settings:
        settings = AutoTradingSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    settings.enabled = payload.enabled
    settings.risk_level = payload.risk_level
    settings.max_trade_size = payload.max_trade_size
    settings.allowed_pairs = ",".join(payload.pairs)
    settings.min_signal_strength = payload.min_signal_strength

    db.commit()
    db.refresh(settings)
    return settings

@router.get("/", response_model=PreferencesOut)
def get_preferences(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return preferences

@router.put("/", response_model=PreferencesOut)
def update_preferences(
    preferences: PreferencesUpdate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_preferences = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not db_preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")

    db_preferences.auto_trade = preferences.auto_trade
    db_preferences.threshold_limit = preferences.threshold_limit
    db.commit()
    db.refresh(db_preferences)
    return db_preferences
