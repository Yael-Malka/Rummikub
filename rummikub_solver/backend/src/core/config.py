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

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://rummikub:rummikub123@localhost:30432/rummikub_db"

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
