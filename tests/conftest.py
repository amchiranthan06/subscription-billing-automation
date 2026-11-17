"""Test setup. Tests use an in-memory SQLite database, so PostgreSQL and Redis are NOT needed."""
import os

os.environ["DATABASE_URL"] = "sqlite://"  # must be set before the app is imported

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401,E402  (registers all tables)
from app.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.routers.billing import get_dispatcher  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def dispatched():
    """Collects the billing cycle ids that would have been sent to Celery."""
    return []


@pytest.fixture()
def client(db_session, dispatched):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_dispatcher] = lambda: dispatched.append
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def make_plan(client):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        payload = {
            "name": f"Plan {counter['n']}",
            "price": "499.00",
            "billing_interval": "monthly",
            "trial_period_days": 14,
            "features": {"max_users": 5},
        }
        payload.update(overrides)
        response = client.post("/plans", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_customer(client):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        payload = {"name": f"Customer {counter['n']}", "email": f"user{counter['n']}@example.com"}
        payload.update(overrides)
        response = client.post("/customers", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_subscription(client):
    def _make(customer_id, plan_id, **overrides):
        payload = {"customer_id": customer_id, "plan_id": plan_id}
        payload.update(overrides)
        response = client.post("/subscriptions", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
