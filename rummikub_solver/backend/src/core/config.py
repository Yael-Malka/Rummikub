"""Backend settings from env vars."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    PROJECT_NAME: str = "Rummikub Solver API"
    REDIRECT_TO_HTTPS: bool = False

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str | None = None
    REDIS_TTL_SECONDS: int = 3600

    # Security & JWT Configuration
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://rummikub:rummikub123@localhost:30432/rummikub_db"

    # SMTP / Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    GMAIL_RUMMIKUB_EMAIL_ADDRESS: str = ""
    GMAIL_RUMMIKUB_APP_PASSWORD: str = ""
    SMTP_FROM: str = "Rummikub Assistant <noreply@rummikub.app>"
    FRONTEND_URL: str = "http://localhost:5180"

    # CORS Configuration
    # Supports parsing a list of strings if provided as JSON, or defaults to standard local development URLs
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5180",
        "http://localhost:5181",
        "http://127.0.0.1:5180",
        "http://127.0.0.1:5181",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
