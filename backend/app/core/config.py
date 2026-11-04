import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "BillFlow Subscription Billing System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "billflow_db"

    # Full Database Connection String
    DATABASE_URL: Optional[str] = None

    def get_database_url(self) -> str:
        """Returns the PostgreSQL connection string."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Business Defaults
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_TRIAL_DAYS: int = 14
    RETRY_SCHEDULE_DAYS: list[int] = [1, 3, 7]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
