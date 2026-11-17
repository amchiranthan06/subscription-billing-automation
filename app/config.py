"""Application settings. Values come from environment variables or the .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://billing_user:billing_pass@localhost:5432/billing_db"
    redis_url: str = "redis://localhost:6379/0"
    billing_scan_interval_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
