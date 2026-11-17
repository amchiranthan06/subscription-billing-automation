"""Subscription lifecycle: create, change plan, pause, resume, cancel, status changes."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import log_event
from app.enums import PlanStatus, SubscriptionStatus
from app.errors import BadRequestError, ConflictError, NotFoundError
from app.models import Customer, Plan, Subscription
from app.services.billing_cycle_service import start_billing_period
from app.state_machine import move_to
from app.utils import utcnow


# ---------------------------------------------------------------- reading
def get_subscription(db: Session, subscription_id: int) -> Subscription:
    sub = db.get(Subscription, subscription_id)
    if sub is None:
        raise NotFoundError(f"Subscription {subscription_id} not found")
    return sub


def list_subscriptions(
    db: Session,
    customer_id: Optional[int] = None,
    status: Optional[SubscriptionStatus] = None,
) -> list[Subscription]:
    stmt = select(Subscription).order_by(Subscription.id)
    if customer_id is not None:
        stmt = stmt.where(Subscription.customer_id == customer_id)
    if status is not None:
        stmt = stmt.where(Subscription.status == status)
    return list(db.scalars(stmt).all())


def _require_not_cancelled(sub: Subscription) -> None:
    if sub.status == SubscriptionStatus.CANCELLED:
        raise ConflictError("Subscription is cancelled; no further changes are allowed")


# ------------------------------------------------- shared internal helpers
def apply_pending_plan(db: Session, sub: Subscription) -> bool:
    """If a plan change was scheduled for the next cycle, switch to that plan now."""
    if sub.pending_plan_id is None:
        return False
    old_plan_id = sub.plan_id
    new_plan = sub.pending_plan
    sub.plan = new_plan
    sub.pending_plan = None
    db.flush()
    log_event(
        db,
        action="subscription.plan_changed",
        entity_type="subscription",
        entity_id=sub.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        old_value={"plan_id": old_plan_id},
        new_value={"plan_id": new_plan.id, "note": "scheduled plan change took effect"},
    )
    return True


def apply_transition(
    db: Session,
    sub: Subscription,
    new_status: SubscriptionStatus,
    *,
    now: datetime,
    reason: Optional[str] = None,
    period_start: Optional[datetime] = None,
    actor: str = "system",
) -> None:
    """Change a subscription's status using the state machine, with side effects and audit log.

    The caller is responsible for committing.
    """
    old_status = sub.status
    move_to(sub, new_status, now)  # raises InvalidTransitionError for illegal changes

    if new_status == SubscriptionStatus.CANCELLED:
        sub.is_paused = False
        sub.paused_at = None
        sub.pending_plan = None
    elif old_status == SubscriptionStatus.TRIAL and new_status == SubscriptionStatus.ACTIVE:
        if period_start is None:  # trial converted early, before its natural end
            period_start = now
            sub.trial_end = now
        apply_pending_plan(db, sub)
        start_billing_period(db, sub, period_start)

    log_event(
        db,
        action="subscription.status_changed",
        entity_type="subscription",
        entity_id=sub.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        old_value={"status": old_status.value},
        new_value={"status": new_status.value, "reason": reason},
        actor=actor,
    )


# --------------------------------------------------------------- creating
def create_subscription(
    db: Session,
    customer_id: int,
    plan_id: int,
    start_trial: bool = True,
    now: Optional[datetime] = None,
) -> Subscription:
    now = now or utcnow()
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise NotFoundError(f"Customer {customer_id} not found")
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NotFoundError(f"Plan {plan_id} not found")
    if plan.status != PlanStatus.ACTIVE:
        raise ConflictError("This plan is archived and cannot accept new subscriptions")

    sub = Subscription(customer_id=customer.id, plan=plan, status_changed_at=now)

    if start_trial and plan.trial_period_days > 0:
        sub.status = SubscriptionStatus.TRIAL
        sub.trial_started_at = now
        sub.trial_end = now + timedelta(days=plan.trial_period_days)
        sub.current_period_start = now
        sub.current_period_end = sub.trial_end
        db.add(sub)
        db.flush()
    else:
        sub.status = SubscriptionStatus.ACTIVE
        sub.activated_at = now
        db.add(sub)
        db.flush()
        start_billing_period(db, sub, now)  # first paid period starts immediately

    log_event(
        db,
        action="subscription.created",
        entity_type="subscription",
        entity_id=sub.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        new_value={
            "status": sub.status.value,
            "plan_id": plan.id,
            "trial_end": sub.trial_end,
            "current_period_end": sub.current_period_end,
        },
    )
    db.commit()
    db.refresh(sub)
    return sub


# ------------------------------------------------------------ change plan
def change_plan(
    db: Session,
    subscription_id: int,
    new_plan_id: int,
    effective: str = "immediate",
) -> Subscription:
    """Switch plan now, or schedule the switch for the next billing cycle.

    Proration (credit for unused time) is part of Milestone 2, so an immediate
    change here only swaps the plan; it does not calculate any credit.
    """
    sub = get_subscription(db, subscription_id)
    _require_not_cancelled(sub)
    new_plan = db.get(Plan, new_plan_id)
    if new_plan is None:
        raise NotFoundError(f"Plan {new_plan_id} not found")
    if new_plan.status != PlanStatus.ACTIVE:
        raise ConflictError("Cannot switch to an archived plan")
    if new_plan.id == sub.plan_id:
        raise BadRequestError("Subscription is already on this plan")

    if effective == "immediate":
        old_plan_id = sub.plan_id
        sub.plan = new_plan
        sub.pending_plan = None
        log_event(
            db,
            action="subscription.plan_changed",
            entity_type="subscription",
            entity_id=sub.id,
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            old_value={"plan_id": old_plan_id},
            new_value={"plan_id": new_plan.id, "effective": "immediate"},
            actor="api",
        )
    else:
        sub.pending_plan = new_plan
        log_event(
            db,
            action="subscription.plan_change_scheduled",
            entity_type="subscription",
            entity_id=sub.id,
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            old_value={"plan_id": sub.plan_id},
            new_value={"plan_id": new_plan.id, "effective_at": sub.current_period_end},
            actor="api",
        )
    db.commit()
    db.refresh(sub)
    return sub


# ----------------------------------------------------------- pause/resume
def pause_subscription(db: Session, subscription_id: int, now: Optional[datetime] = None) -> Subscription:
    now = now or utcnow()
    sub = get_subscription(db, subscription_id)
    if sub.status != SubscriptionStatus.ACTIVE:
        raise ConflictError("Only active subscriptions can be paused")
    if sub.is_paused:
        raise ConflictError("Subscription is already paused")
    if sub.cancel_at_period_end:
        raise ConflictError("Cancellation is already scheduled for the end of the cycle")

    sub.is_paused = True
    sub.paused_at = now
    log_event(
        db,
        action="subscription.paused",
        entity_type="subscription",
        entity_id=sub.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        new_value={"paused_at": now},
        actor="api",
    )
    db.commit()
    db.refresh(sub)
    return sub


def resume_subscription(db: Session, subscription_id: int, now: Optional[datetime] = None) -> Subscription:
    """Resume a paused subscription. The current period is extended by the time it was paused."""
    now = now or utcnow()
    sub = get_subscription(db, subscription_id)
    if not sub.is_paused:
        raise ConflictError("Subscription is not paused")

    paused_for = now - sub.paused_at
    if paused_for < timedelta(0):
        paused_for = timedelta(0)
    old_end = sub.current_period_end
    sub.current_period_end = old_end + paused_for
    sub.is_paused = False
    sub.paused_at = None
    log_event(
        db,
        action="subscription.resumed",
        entity_type="subscription",
        entity_id=sub.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        old_value={"current_period_end": old_end},
        new_value={"current_period_end": sub.current_period_end, "paused_seconds": int(paused_for.total_seconds())},
        actor="api",
    )
    db.commit()
    db.refresh(sub)
    return sub


# ----------------------------------------------------------------- cancel
def cancel_subscription(
    db: Session,
    subscription_id: int,
    timing: str = "immediate",
    reason: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Subscription:
    """Cancel now, or at the end of the current cycle (trial or billing period)."""
    now = now or utcnow()
    sub = get_subscription(db, subscription_id)
    if sub.status == SubscriptionStatus.CANCELLED:
        raise ConflictError("Subscription is already cancelled")

    if timing == "immediate":
        sub.cancel_at_period_end = False
        apply_transition(
            db,
            sub,
            SubscriptionStatus.CANCELLED,
            now=now,
            reason=reason or "Cancelled immediately",
            actor="api",
        )
    else:
        if sub.is_paused:
            raise ConflictError("Resume the subscription first, or cancel immediately")
        if not sub.cancel_at_period_end:
            sub.cancel_at_period_end = True
            log_event(
                db,
                action="subscription.cancel_scheduled",
                entity_type="subscription",
                entity_id=sub.id,
                customer_id=sub.customer_id,
                subscription_id=sub.id,
                new_value={"effective_at": sub.current_period_end, "reason": reason},
                actor="api",
            )
    db.commit()
    db.refresh(sub)
    return sub


# ------------------------------------------------- manual status change
def transition_subscription(
    db: Session,
    subscription_id: int,
    to_status: SubscriptionStatus,
    reason: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Subscription:
    """Admin/testing helper: request any status change; the state machine decides if it is allowed."""
    sub = get_subscription(db, subscription_id)
    apply_transition(db, sub, to_status, now=now or utcnow(), reason=reason, actor="admin")
    db.commit()
    db.refresh(sub)
    return sub
