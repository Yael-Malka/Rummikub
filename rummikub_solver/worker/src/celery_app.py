"""Celery app wiring for the worker."""

import os

from celery import Celery
from celery.signals import worker_process_init
from src.config import settings

celery_app = Celery(
    "rummikub_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_transport_options={"master_name": "mymaster"},
    result_backend_transport_options={"master_name": "mymaster"},
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=settings.PROCESSING_TIMEOUT_SECONDS,
    task_time_limit=settings.PROCESSING_TIMEOUT_SECONDS + settings.PROCESSING_TIMEOUT_GRACE_SECONDS,
    task_acks_late=True,
)

celery_app.autodiscover_tasks(["src"])


@worker_process_init.connect
def _preload_inference_models(**_kwargs) -> None:
    """Load YOLO + CNN into memory when a worker child process starts.
    Avoids a multi-second stall on the first recognition task after deploy.
    """
    from inference.reconstruct_board import warmup_models

    models_dir = os.path.abspath(settings.MODELS_DIR)
    warmup_models(models_dir)
