from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
from app.api import auth_router, portfolio as portfolio_router, trading, live_feeds, alerts
from app.api.preferences import router as preferences_router
from app.core.database import engine, Base
from app.models.portfolio import Portfolio
from app.models.preferences import Preferences
from app.tasks import celery
from celery.schedules import crontab

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables during startup
    Base.metadata.create_all(bind=engine)
    Portfolio.metadata.create_all(bind=engine)
    Preferences.metadata.create_all(bind=engine)

    # Setup Celery beat schedule
    celery.conf.beat_schedule = {
        "validate-binance-keys": {
            "task": "app.tasks.trading_tasks.validate_user_binance_keys",
            "schedule": crontab(hour=0, minute=0),
            "args": ("testuser@example.com",)
        },
        "check-price-decline": {
            "task": "app.tasks.alert_tasks.check_price_decline",
            "schedule": crontab(minute="*/15"),
            "args": ("testuser@example.com", "BTC/USDT", 0.05)
        }
    }

    yield  # Application is now running

# Initialize FastAPI app
app = FastAPI(title="Bitcoin Trading Backend", lifespan=lifespan)

# Register API routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(trading, prefix="/trading", tags=["trading"])
app.include_router(live_feeds, prefix="/live", tags=["live"])
app.include_router(preferences_router, prefix="/preferences", tags=["preferences"])
app.include_router(alerts, prefix="/alerts", tags=["alerts"])

@app.get("/")
def root():
    return {"message": "Bitcoin Trading Backend is running"}
