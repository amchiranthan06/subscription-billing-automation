from datetime import datetime, timezone
from typing import Optional
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Subscription, Plan, BillingCycle
from app.models.enums import BillingInterval, BillingCycleStatus, SubscriptionStatus
from app.services.audit import create_audit_log

def calculate_next_renewal_date(start_date: datetime, interval: BillingInterval) -> datetime:
    """
    Task 9 Requirement:
    - Monthly plans calculate next renewal date (+1 month with proper calendar boundary handling)
    - Annual plans calculate next renewal date (+1 year with leap-year handling)
    """
    if interval == BillingInterval.ANNUAL:
        return start_date + relativedelta(years=1)
    elif interval == BillingInterval.MONTHLY:
        return start_date + relativedelta(months=1)
    else:
        raise ValueError(f"Unsupported billing interval: {interval}")

def generate_billing_cycle(
    db: Session,
    subscription_id: str,
    auto_complete_previous: bool = True
) -> BillingCycle:
    """
    Task 9 Requirement:
    - Generates and stores sequential billing cycle records for subscriptions.
    - Preserves complete billing cycle history.
    - Updates subscription current period end date.
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID '{subscription_id}' not found."
        )

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan associated with subscription not found."
        )

    # Fetch existing cycles ordered by index to maintain full history
    existing_cycles = (
        db.query(BillingCycle)
        .filter(BillingCycle.subscription_id == subscription.id)
        .order_by(BillingCycle.cycle_index.desc())
        .all()
    )

    if not existing_cycles:
        # First billing cycle
        cycle_index = 1
        cycle_start = subscription.start_date
    else:
        latest_cycle = existing_cycles[0]
        # Auto-complete the preceding cycle if requested
        if auto_complete_previous and latest_cycle.status == BillingCycleStatus.PENDING:
            latest_cycle.status = BillingCycleStatus.COMPLETED
            latest_cycle.updated_at = datetime.now(timezone.utc)
            db.add(latest_cycle)
        
        cycle_index = latest_cycle.cycle_index + 1
        cycle_start = latest_cycle.cycle_end_date

    # Compute renewal date based on plan interval
    cycle_end = calculate_next_renewal_date(cycle_start, plan.billing_interval)
    renewal_date = cycle_end

    new_cycle = BillingCycle(
        subscription_id=subscription.id,
        cycle_index=cycle_index,
        cycle_start_date=cycle_start,
        cycle_end_date=cycle_end,
        renewal_date=renewal_date,
        status=BillingCycleStatus.PENDING
    )
    db.add(new_cycle)

    # Update subscription end_date
    subscription.end_date = cycle_end
    subscription.updated_at = datetime.now(timezone.utc)
    db.add(subscription)

    db.commit()
    db.refresh(new_cycle)

    # Automatically generate audit log for cycle creation
    create_audit_log(
        db=db,
        entity_type="billing_cycle",
        entity_id=new_cycle.id,
        action="billing_cycle_generated",
        old_value=None,
        new_value={
            "cycle_index": cycle_index,
            "interval": plan.billing_interval.value,
            "cycle_start_date": cycle_start.isoformat(),
            "cycle_end_date": cycle_end.isoformat(),
            "renewal_date": renewal_date.isoformat()
        },
        performed_by="billing_cycle_engine",
        customer_id=subscription.customer_id,
        subscription_id=subscription.id
    )

    return new_cycle

def get_billing_cycle_history(db: Session, subscription_id: str) -> list[BillingCycle]:
    """
    Task 9 Requirement:
    - Store and retrieve complete billing cycle history for any subscription.
    """
    return (
        db.query(BillingCycle)
        .filter(BillingCycle.subscription_id == subscription_id)
        .order_by(BillingCycle.cycle_index.asc())
        .all()
    )
