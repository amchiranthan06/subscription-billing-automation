from datetime import datetime, timedelta, timezone

from app.services.scheduler_service import run_billing_scan


def now() -> datetime:
    return datetime.now(timezone.utc)


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def run_scan(client, as_of: datetime) -> dict:
    response = client.post("/billing/run-scan", json={"as_of": as_of.isoformat()})
    assert response.status_code == 200, response.text
    return response.json()


def test_scan_with_nothing_to_do(client, dispatched):
    response = client.post("/billing/run-scan")  # no body: uses the current time
    assert response.status_code == 200
    body = response.json()
    assert body["trials_converted"] == 0
    assert body["renewals_created"] == 0
    assert body["invoice_jobs_dispatched"] == 0
    assert body["errors"] == 0
    assert dispatched == []


def test_trial_converts_to_active_and_triggers_invoice_job(
    client, make_plan, make_customer, make_subscription, dispatched
):
    plan = make_plan(trial_period_days=14)
    sub = make_subscription(make_customer()["id"], plan["id"])

    # Trial still running: nothing happens
    early = run_scan(client, now() + timedelta(days=5))
    assert early["trials_converted"] == 0
    assert dispatched == []

    # Trial over: becomes active, first cycle created, invoice job triggered
    later = run_scan(client, now() + timedelta(days=15))
    assert later["trials_converted"] == 1
    assert later["invoice_jobs_dispatched"] == 1
    assert later["errors"] == 0
    assert len(dispatched) == 1

    after = client.get(f"/subscriptions/{sub['id']}").json()
    assert after["status"] == "active"
    assert after["activated_at"] is not None
    assert parse(after["current_period_start"]) == parse(sub["trial_end"])  # billing starts when trial ends

    cycles = client.get(f"/billing/cycles?subscription_id={sub['id']}").json()
    assert len(cycles) == 1
    assert cycles[0]["invoice_job_triggered_at"] is not None

    # Running the scan again does nothing new (idempotent)
    again = run_scan(client, now() + timedelta(days=15))
    assert again["trials_converted"] == 0
    assert again["invoice_jobs_dispatched"] == 0
    assert len(dispatched) == 1


def test_monthly_renewal_creates_next_cycle(client, make_plan, make_customer, make_subscription, dispatched):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])  # active, cycle 1 created

    # Before the period ends: only the first cycle's invoice job is sent
    first = run_scan(client, now())
    assert first["renewals_created"] == 0
    assert first["invoice_jobs_dispatched"] == 1

    # After the period ends: cycle 2 is created and its job is sent
    renewal = run_scan(client, now() + timedelta(days=40))
    assert renewal["renewals_created"] == 1
    assert renewal["invoice_jobs_dispatched"] == 1
    assert len(dispatched) == 2

    cycles = client.get(f"/billing/cycles?subscription_id={sub['id']}").json()
    assert [c["cycle_number"] for c in cycles] == [1, 2]
    assert parse(cycles[1]["period_start"]) == parse(cycles[0]["period_end"])  # no gap between cycles


def test_annual_plan_renews_after_one_year(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0, billing_interval="annual", price="4999.00")
    make_subscription(make_customer()["id"], plan["id"])

    assert run_scan(client, now() + timedelta(days=40))["renewals_created"] == 0
    assert run_scan(client, now() + timedelta(days=370))["renewals_created"] == 1


def test_cancel_at_end_of_cycle_is_applied_by_scan(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])
    client.post(f"/subscriptions/{sub['id']}/cancel", json={"timing": "end_of_cycle"})

    result = run_scan(client, now() + timedelta(days=40))
    assert result["cancellations_applied"] == 1
    assert result["renewals_created"] == 0

    after = client.get(f"/subscriptions/{sub['id']}").json()
    assert after["status"] == "cancelled"
    assert after["cancelled_at"] is not None


def test_paused_subscription_is_not_renewed(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])
    client.post(f"/subscriptions/{sub['id']}/pause")

    result = run_scan(client, now() + timedelta(days=40))
    assert result["renewals_created"] == 0
    assert client.get(f"/subscriptions/{sub['id']}").json()["status"] == "active"


def test_scheduled_plan_change_applies_at_renewal(client, make_plan, make_customer, make_subscription):
    plan_a = make_plan(trial_period_days=0)
    plan_b = make_plan(trial_period_days=0, price="999.00")
    sub = make_subscription(make_customer()["id"], plan_a["id"])
    client.post(
        f"/subscriptions/{sub['id']}/change-plan",
        json={"new_plan_id": plan_b["id"], "effective": "next_cycle"},
    )

    result = run_scan(client, now() + timedelta(days=40))
    assert result["renewals_created"] == 1

    after = client.get(f"/subscriptions/{sub['id']}").json()
    assert after["plan_id"] == plan_b["id"]
    assert after["pending_plan_id"] is None
    cycles = client.get(f"/billing/cycles?subscription_id={sub['id']}").json()
    assert cycles[-1]["plan_id"] == plan_b["id"]


def test_failed_dispatch_is_retried_on_next_scan(client, db_session, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    make_subscription(make_customer()["id"], plan["id"])

    def broken_dispatch(_cycle_id):
        raise RuntimeError("message broker is down")

    first = run_billing_scan(db_session, now(), broken_dispatch)
    assert first.errors == 1
    assert first.invoice_jobs_dispatched == 0

    sent = []
    second = run_billing_scan(db_session, now(), sent.append)
    assert second.errors == 0
    assert second.invoice_jobs_dispatched == 1
    assert len(sent) == 1


def test_scan_events_are_audited(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])
    run_scan(client, now())

    actions = [e["action"] for e in client.get(f"/audit-logs?subscription_id={sub['id']}").json()]
    assert "billing_cycle.created" in actions
    assert "billing_cycle.invoice_job_triggered" in actions


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}
