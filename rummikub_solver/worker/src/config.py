"""Worker settings (DB, Redis, S3, model paths)."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database Configuration (PostgreSQL - sync)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://rummikub:rummikub123@localhost:30432/rummikub_db"
    )

    # S3 Configuration
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:30900")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin123")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "rummikub-boards")

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:31660/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:31660/0")

    # Processing Timeout Configuration
    PROCESSING_TIMEOUT_SECONDS: int = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "120"))
    PROCESSING_TIMEOUT_GRACE_SECONDS: int = int(os.getenv("PROCESSING_TIMEOUT_GRACE_SECONDS", "15"))

    # Models Directory
    MODELS_DIR: str = os.getenv("MODELS_DIR", "./models")

    # Redis Status Storage
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "31660"))
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", "3600"))

settings = Settings()
