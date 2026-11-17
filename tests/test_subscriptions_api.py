from datetime import datetime, timedelta


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_create_subscription_with_trial(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    customer = make_customer()
    sub = make_subscription(customer["id"], plan["id"])

    assert sub["status"] == "trial"
    assert sub["trial_end"] is not None
    assert parse(sub["trial_end"]) - parse(sub["trial_started_at"]) == timedelta(days=14)
    assert sub["status_changed_at"] is not None
    # no billing cycle while the customer is on a free trial
    assert client.get(f"/billing/cycles?subscription_id={sub['id']}").json() == []


def test_create_subscription_without_trial_starts_active(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    customer = make_customer()
    sub = make_subscription(customer["id"], plan["id"])

    assert sub["status"] == "active"
    assert sub["activated_at"] is not None
    assert sub["current_period_end"] is not None
    cycles = client.get(f"/billing/cycles?subscription_id={sub['id']}").json()
    assert len(cycles) == 1
    assert cycles[0]["cycle_number"] == 1
    assert cycles[0]["status"] == "pending"


def test_start_trial_false_skips_trial(make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    customer = make_customer()
    sub = make_subscription(customer["id"], plan["id"], start_trial=False)
    assert sub["status"] == "active"


def test_unknown_customer_or_plan(client, make_plan, make_customer):
    plan = make_plan()
    customer = make_customer()
    assert client.post("/subscriptions", json={"customer_id": 999, "plan_id": plan["id"]}).status_code == 404
    assert client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": 999}).status_code == 404


def test_archived_plan_cannot_get_new_subscription(client, make_plan, make_customer):
    plan = make_plan()
    customer = make_customer()
    client.post(f"/plans/{plan['id']}/archive")
    response = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert response.status_code == 409


def test_pause_and_resume(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])

    paused = client.post(f"/subscriptions/{sub['id']}/pause")
    assert paused.status_code == 200
    assert paused.json()["is_paused"] is True
    assert paused.json()["paused_at"] is not None
    assert client.post(f"/subscriptions/{sub['id']}/pause").status_code == 409  # already paused

    resumed = client.post(f"/subscriptions/{sub['id']}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["is_paused"] is False
    assert resumed.json()["paused_at"] is None
    assert parse(resumed.json()["current_period_end"]) >= parse(sub["current_period_end"])
    assert client.post(f"/subscriptions/{sub['id']}/resume").status_code == 409  # not paused


def test_only_active_subscriptions_can_be_paused(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    sub = make_subscription(make_customer()["id"], plan["id"])  # still in trial
    assert client.post(f"/subscriptions/{sub['id']}/pause").status_code == 409


def test_change_plan_immediately(client, make_plan, make_customer, make_subscription):
    plan_a = make_plan(trial_period_days=0)
    plan_b = make_plan(trial_period_days=0, price="999.00")
    sub = make_subscription(make_customer()["id"], plan_a["id"])

    response = client.post(
        f"/subscriptions/{sub['id']}/change-plan",
        json={"new_plan_id": plan_b["id"], "effective": "immediate"},
    )
    assert response.status_code == 200
    assert response.json()["plan_id"] == plan_b["id"]

    same = client.post(
        f"/subscriptions/{sub['id']}/change-plan", json={"new_plan_id": plan_b["id"]}
    )
    assert same.status_code == 400


def test_change_plan_next_cycle_only_schedules(client, make_plan, make_customer, make_subscription):
    plan_a = make_plan(trial_period_days=0)
    plan_b = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan_a["id"])

    response = client.post(
        f"/subscriptions/{sub['id']}/change-plan",
        json={"new_plan_id": plan_b["id"], "effective": "next_cycle"},
    )
    assert response.status_code == 200
    assert response.json()["plan_id"] == plan_a["id"]
    assert response.json()["pending_plan_id"] == plan_b["id"]


def test_cancel_immediately(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    sub = make_subscription(make_customer()["id"], plan["id"])

    response = client.post(f"/subscriptions/{sub['id']}/cancel", json={"timing": "immediate"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancelled_at"] is not None

    assert client.post(f"/subscriptions/{sub['id']}/cancel", json={}).status_code == 409
    assert client.post(f"/subscriptions/{sub['id']}/pause").status_code == 409
    change = client.post(f"/subscriptions/{sub['id']}/change-plan", json={"new_plan_id": plan["id"]})
    assert change.status_code == 409


def test_cancel_at_end_of_cycle(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=0)
    sub = make_subscription(make_customer()["id"], plan["id"])

    response = client.post(f"/subscriptions/{sub['id']}/cancel", json={"timing": "end_of_cycle"})
    assert response.status_code == 200
    assert response.json()["status"] == "active"  # still active until the cycle ends
    assert response.json()["cancel_at_period_end"] is True


def test_transition_endpoint_enforces_state_machine(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    sub = make_subscription(make_customer()["id"], plan["id"])
    url = f"/subscriptions/{sub['id']}/transition"

    # trial -> past_due is not allowed
    assert client.post(url, json={"to_status": "past_due"}).status_code == 409

    # trial -> active is allowed and opens the first billing cycle
    response = client.post(url, json={"to_status": "active", "reason": "customer upgraded early"})
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["activated_at"] is not None
    assert len(client.get(f"/billing/cycles?subscription_id={sub['id']}").json()) == 1

    # active -> past_due -> cancelled
    past_due = client.post(url, json={"to_status": "past_due"})
    assert past_due.status_code == 200
    assert past_due.json()["past_due_at"] is not None
    cancelled = client.post(url, json={"to_status": "cancelled"})
    assert cancelled.status_code == 200

    # cancelled is final
    assert client.post(url, json={"to_status": "active"}).status_code == 409


def test_audit_log_records_changes(client, make_plan, make_customer, make_subscription):
    plan = make_plan(trial_period_days=14)
    customer = make_customer()
    sub = make_subscription(customer["id"], plan["id"])
    client.post(f"/subscriptions/{sub['id']}/cancel", json={"timing": "immediate"})

    logs = client.get(f"/audit-logs?subscription_id={sub['id']}").json()
    actions = [entry["action"] for entry in logs]
    assert "subscription.created" in actions
    assert "subscription.status_changed" in actions

    changed = next(entry for entry in logs if entry["action"] == "subscription.status_changed")
    assert changed["old_value"]["status"] == "trial"
    assert changed["new_value"]["status"] == "cancelled"

    by_customer = client.get(f"/audit-logs?customer_id={customer['id']}").json()
    assert len(by_customer) >= len(logs)
