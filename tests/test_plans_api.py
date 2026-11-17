from decimal import Decimal


def test_create_plan(make_plan):
    plan = make_plan(name="Starter", price="499.00", features={"max_users": 3, "support": "email"})
    assert plan["status"] == "active"
    assert plan["billing_interval"] == "monthly"
    assert Decimal(plan["price"]) == Decimal("499.00")
    assert plan["features"] == {"max_users": 3, "support": "email"}
    assert plan["trial_period_days"] == 14


def test_annual_plan(make_plan):
    plan = make_plan(name="Yearly", billing_interval="annual", price="4999.00")
    assert plan["billing_interval"] == "annual"


def test_duplicate_plan_name_rejected(client, make_plan):
    make_plan(name="Pro")
    response = client.post("/plans", json={"name": "Pro", "price": "10", "billing_interval": "monthly"})
    assert response.status_code == 409


def test_invalid_plan_input_rejected(client):
    bad_price = client.post("/plans", json={"name": "X", "price": "-5", "billing_interval": "monthly"})
    assert bad_price.status_code == 422
    bad_interval = client.post("/plans", json={"name": "Y", "price": "5", "billing_interval": "weekly"})
    assert bad_interval.status_code == 422


def test_update_plan(client, make_plan):
    plan = make_plan(name="Basic")
    response = client.patch(
        f"/plans/{plan['id']}",
        json={"price": "599.00", "trial_period_days": 7, "features": {"max_users": 10}},
    )
    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["price"]) == Decimal("599.00")
    assert body["trial_period_days"] == 7
    assert body["features"] == {"max_users": 10}


def test_billing_interval_cannot_be_changed(client, make_plan):
    plan = make_plan()
    response = client.patch(f"/plans/{plan['id']}", json={"billing_interval": "annual"})
    assert response.status_code == 422


def test_empty_update_rejected(client, make_plan):
    plan = make_plan()
    assert client.patch(f"/plans/{plan['id']}", json={}).status_code == 400


def test_archive_plan(client, make_plan):
    plan = make_plan(name="Old")
    response = client.post(f"/plans/{plan['id']}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"
    assert response.json()["archived_at"] is not None

    # archived plans are hidden by default, but can be listed on request
    assert plan["id"] not in [p["id"] for p in client.get("/plans").json()]
    assert plan["id"] in [p["id"] for p in client.get("/plans?include_archived=true").json()]

    # archived plans cannot be edited or archived again
    assert client.patch(f"/plans/{plan['id']}", json={"price": "1"}).status_code == 409
    assert client.post(f"/plans/{plan['id']}/archive").status_code == 409


def test_get_unknown_plan_404(client):
    assert client.get("/plans/999").status_code == 404
