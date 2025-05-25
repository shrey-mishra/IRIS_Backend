from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from app.services.auth_service import update_binance_keys
from app.utils.crypto_utils import decrypt
from app.utils.binance_utils import get_wallet_balances
from fastapi.responses import RedirectResponse
from app.schemas.user import UserCreate, UserOut, UserLogin, BinanceKeys, UserStatsOut, UserOutRegister
from app.models.user import UserStats
from app.services.auth_service import create_user, authenticate_user, get_user_by_email, delete_user, validate_binance_keys
from app.core.security import create_access_token, get_current_user
from app.core.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
import requests
from cryptography.fernet import Fernet
import redis
from ccxt import binance
import uuid
from pydantic import BaseModel

router = APIRouter()

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

# Redis client for token blacklisting
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@router.post("/register", response_model=UserOutRegister)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return UserOutRegister.from_orm(db_user)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.from_orm(db_user)}

@router.post("/logout")
def logout(current_user_email: str = Depends(get_current_user)):
    try:
        redis_client.setex(current_user_email, 3600, "blacklisted")
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Redis server not reachable")
    return {"message": "Logged out"}

@router.delete("/user")
def delete_account(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    delete_user(db, db_user)
    return {"message": "Account deleted"}

@router.post("/binance_keys")
def update_binance_keys_endpoint(
    binance_keys: BinanceKeys,
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

@router.get("/validate-binance-account")
def validate_binance_account(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, current_user_email)
    if not user or not user.binance_api_key or not user.binance_api_secret:
        raise HTTPException(status_code=404, detail="API keys not found")

    try:
        wallets = get_wallet_balances(user)
        return {"status": "success", "wallets": wallets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Binance keys or API error: {str(e)}")

@router.get("/userstats", response_model=UserStatsOut)
def get_user_stats(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
    if not user_stats:
        user_stats = UserStats(user_id=user.id)
        db.add(user_stats)
        db.commit()
        db.refresh(user_stats)

    return user_stats

@router.get("/userinfo")
def get_user_info(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserOut.from_orm(user)

@router.post("/change-password")
def change_password(
    password_change: ChangePassword,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, current_user_email, password_change.current_password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect current password")

    hashed_password = pwd_context.hash(password_change.new_password)
    user.hashed_password = hashed_password
    db.commit()
    return {"message": "Password changed successfully"}
