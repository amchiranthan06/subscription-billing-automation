"""Create all database tables.  Run from the project folder:  python -m scripts.init_db"""
from app.database import Base, engine
import app.models  # noqa: F401  (importing registers every table with SQLAlchemy)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables are ready:")
    for table_name in Base.metadata.tables:
        print("  -", table_name)


if __name__ == "__main__":
    main()
