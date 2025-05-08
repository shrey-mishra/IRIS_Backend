from sqlalchemy import Column, Integer, String
from app.core.database import Base
from cryptography.fernet import Fernet
# app/models/user.p

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    binance_api_key = Column(String, nullable=True)
    binance_api_secret = Column(String, nullable=True)
 # Optional for now

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    roi = Column(Integer, default=0)
    total_assets = Column(Integer, default=0)
    total_loss = Column(Integer, default=0)
