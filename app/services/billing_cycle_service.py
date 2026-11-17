"""Billing cycle helpers: period maths and creating billing_cycles rows."""
from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import log_event
from app.enums import BillingCycleStatus, BillingInterval
from app.models import BillingCycle, Subscription


def add_interval(start: datetime, interval: BillingInterval) -> datetime:
    """Return the end of a billing period that starts at `start`."""
    if interval == BillingInterval.MONTHLY:
        return start + relativedelta(months=1)
    if interval == BillingInterval.ANNUAL:
        return start + relativedelta(years=1)
    raise ValueError(f"Unsupported billing interval: {interval}")


def start_billing_period(db: Session, sub: Subscription, period_start: datetime) -> BillingCycle:
    """Open a new billing period for a subscription and create its billing_cycles row.

    The cycle starts as 'pending'. The scheduler then triggers an invoice-generation
    job for it (see scheduler_service.run_billing_scan).
    """
    plan = sub.plan
    period_end = add_interval(period_start, plan.billing_interval)
    sub.current_period_start = period_start
    sub.current_period_end = period_end

    already = db.scalar(
        select(func.count()).select_from(BillingCycle).where(BillingCycle.subscription_id == sub.id)
    )
    cycle = BillingCycle(
        subscription_id=sub.id,
        plan_id=plan.id,
        cycle_number=(already or 0) + 1,
        period_start=period_start,
        period_end=period_end,
        status=BillingCycleStatus.PENDING,
    )
    db.add(cycle)
    db.flush()

    log_event(
        db,
        action="billing_cycle.created",
        entity_type="billing_cycle",
        entity_id=cycle.id,
        customer_id=sub.customer_id,
        subscription_id=sub.id,
        new_value={
            "cycle_number": cycle.cycle_number,
            "plan_id": plan.id,
            "period_start": period_start,
            "period_end": period_end,
        },
    )
    return cycle
