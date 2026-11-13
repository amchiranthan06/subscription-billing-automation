import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("billflow")
db_url = settings.get_database_url()

def init_engine():
    global db_url
    if db_url.startswith("postgresql"):
        try:
            test_engine = create_engine(
                db_url,
                connect_args={"connect_timeout": 2},
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            with test_engine.connect() as conn:
                pass
            return test_engine
        except Exception as e:
            logger.warning(
                f"PostgreSQL connection to {db_url} unavailable ({e}). Falling back to local SQLite database."
            )
            sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "billflow.db"))
            db_url = f"sqlite:///{sqlite_path}"
            return create_engine(db_url, connect_args={"check_same_thread": False})
    elif db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url)

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides an isolated database session per request,
    and automatically closes it when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """
    Tests the active database connection.
    Returns status and connection details.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            is_pg = str(engine.url).startswith("postgresql")
            return {
                "status": "connected",
                "database": "PostgreSQL" if is_pg else "SQLite",
                "host": settings.POSTGRES_HOST if is_pg else "local",
                "database_name": settings.POSTGRES_DB if is_pg else "billflow.db",
                "ping": "successful"
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "database": "PostgreSQL" if str(engine.url).startswith("postgresql") else "SQLite",
            "host": settings.POSTGRES_HOST,
            "database_name": settings.POSTGRES_DB,
            "error": str(e)
        }
