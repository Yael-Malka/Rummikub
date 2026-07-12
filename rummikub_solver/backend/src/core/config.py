"""Backend settings from env vars."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    PROJECT_NAME: str = "Rummikub Solver API"
    REDIRECT_TO_HTTPS: bool = False

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
