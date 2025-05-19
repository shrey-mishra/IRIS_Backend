# app/tasks/__init__.py

from celery import Celery
from app.core.config import settings

# Step 1: Define Celery app first
celery = Celery(
    "bitcoin_trading",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks.trading_tasks"]  # optional: auto-import other task files
)

# Step 2: Configure the app
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Step 3: Explicitly import shared task modules to register them
from app.tasks.scheduler import run_auto_trading_all_users  
