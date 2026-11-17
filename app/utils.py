"""Small helpers shared across the project."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime. All timestamps in this project are UTC."""
    return datetime.now(timezone.utc)
