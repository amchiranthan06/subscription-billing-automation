import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "billflow_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.billing_engine", "app.services.retry_engine"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-daily-billing-cycle-check": {
            "task": "app.services.billing_engine.process_due_billing_cycles",
            "schedule": 86400.0, # Every 24 hours
        },
        "run-failed-payment-retries": {
            "task": "app.services.retry_engine.process_pending_retries",
            "schedule": 3600.0, # Every 1 hour
        }
    }
)
