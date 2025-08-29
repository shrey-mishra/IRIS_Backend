from celery import Celery
from celery.schedules import crontab

# Define the Celery app
celery = Celery(
    "bitcoin_trading",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "app.tasks.trading_tasks",
        "app.tasks.alert_tasks",
    ],
)

# Optional: load external celeryconfig.py if present
try:
    celery.config_from_object("celeryconfig")
except Exception:
    pass

# Configure Celery
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat Schedule (runs even without FastAPI)
celery.conf.beat_schedule = {
    "run-auto-trading": {
        "task": "app.tasks.trading_tasks.run_auto_trading_for_all_users",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
        "args": (),
    },
}