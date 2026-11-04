import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

db_url = settings.get_database_url()

# Connection arguments per database engine
connect_args = {}
if db_url.startswith("postgresql"):
    connect_args = {"connect_timeout": 3}
elif db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# SQLAlchemy engine configuration
# pool_pre_ping=True checks that the connection is alive before using it
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

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
    Tests the PostgreSQL connection by executing a simple SELECT 1 query.
    Returns status and connection details.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "database": "PostgreSQL",
                "host": settings.POSTGRES_HOST,
                "database_name": settings.POSTGRES_DB,
                "ping": "successful"
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "database": "PostgreSQL",
            "host": settings.POSTGRES_HOST,
            "database_name": settings.POSTGRES_DB,
            "error": str(e)
        }
