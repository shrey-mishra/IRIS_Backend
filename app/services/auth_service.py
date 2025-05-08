from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import HTTPException
from cryptography.fernet import Fernet
import base64

# Generate a Fernet key (store securely in production, e.g., .env)
key = Fernet.generate_key()
cipher = Fernet(key)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: UserCreate):
    print("create_user called")
    print(f"User: {user}")
    hashed_password = pwd_context.hash(user.password)

    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print("User created successfully")
        return db_user
    except IntegrityError:
        db.rollback()
        print("Email already registered")
        raise HTTPException(status_code=422, detail="Email already registered")

def authenticate_user(db: Session, email: str, password: str):
    print("authenticate_user called")
    print(f"Email: {email}, Password: {password}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("User not found")
        return None
    if not pwd_context.verify(password, user.hashed_password):
        print("Invalid password")
        return None
    print("User authenticated successfully")
    return user

def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

from binance.client import Client
from binance.exceptions import BinanceAPIException

def update_binance_keys(db: Session, user: User, api_key: str, api_secret: str):
    encrypted_api_key = cipher.encrypt(api_key.encode()) if api_key else None
    encrypted_api_secret = cipher.encrypt(api_secret.encode()) if api_secret else None

    user.binance_api_key = encrypted_api_key.decode() if encrypted_api_key else None
    user.binance_api_secret = encrypted_api_secret.decode() if encrypted_api_secret else None

    db.commit()
    db.refresh(user)

def validate_binance_keys(api_key: str, api_secret: str):
    print("validate_binance_keys called")
    print(f"API Key: {api_key}, API Secret: {api_secret}")
    try:
        client = Client(api_key, api_secret)
        print("Client created")
        client.get_account()  # This will trigger an exception if the keys are invalid
        print("Account retrieved")
        return True
    except BinanceAPIException as e:
        print(f"Binance API Exception: {e}")
        return False
    except Exception as e:
        print(f"General Exception: {e}")
        return False
