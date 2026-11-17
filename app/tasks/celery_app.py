"""Celery application and the beat schedule (the billing cycle scheduler)."""
from datetime import timedelta

from celery import Celery

from app.config import settings

celery_app = Celery(
    "billing",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.billing_tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # Every N seconds (default 60) look for subscriptions that are due for billing.
        "scan-billing-cycles": {
            "task": "app.tasks.billing_tasks.scan_billing_cycles",
            "schedule": timedelta(seconds=settings.billing_scan_interval_seconds),
        },
    },
)
