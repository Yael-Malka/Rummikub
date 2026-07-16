"""Celery client used by the API to enqueue tasks."""

from celery import Celery
from src.core.config import settings

broker_url = settings.REDIS_URL if settings.REDIS_URL else settings.CELERY_BROKER_URL
backend_url = settings.REDIS_URL if settings.REDIS_URL else settings.CELERY_RESULT_BACKEND

# Initialize Celery app with same name and broker settings as the worker
celery_app = Celery(
    "rummikub_worker",
    broker=broker_url,
    backend=backend_url,
    broker_transport_options={"master_name": "mymaster"},
    result_backend_transport_options={"master_name": "mymaster"},
)
