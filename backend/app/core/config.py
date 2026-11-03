import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BillFlow Subscription Billing System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database: Defaults to SQLite for immediate local dev, easily swappable to PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./billflow.db")
    
    # Financial & Currency Defaults
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_TRIAL_DAYS: int = 14
    
    # Dunning / Retry Schedule in Days (e.g., Retry 1 on Day 1, Retry 2 on Day 3, Retry 3 on Day 7)
    RETRY_SCHEDULE_DAYS: list[int] = [1, 3, 7]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
