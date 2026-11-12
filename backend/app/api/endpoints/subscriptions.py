from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Customer, Plan, Subscription, BillingCycle, AuditLog
from app.models.enums import SubscriptionStatus, BillingInterval, CancellationTiming
from app.schemas.schemas import (
    SubscriptionCreate, SubscriptionResponse, SubscriptionCancel, SubscriptionStatusTransition
)
from app.services.state_machine import transition_subscription, InvalidStateTransitionError

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

def compute_period_end(start_date: datetime, interval: BillingInterval) -> datetime:
    if interval == BillingInterval.ANNUAL:
        return start_date + relativedelta(years=1)
    return start_date + relativedelta(months=1)

@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(sub_in: SubscriptionCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == sub_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    plan = db.query(Plan).filter(Plan.id == sub_in.plan_id).first()
    if not plan or not plan.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active plan required")

    now = datetime.now(timezone.utc)
    trial_days = sub_in.custom_trial_days if sub_in.custom_trial_days is not None else plan.trial_days

    if sub_in.start_with_trial and trial_days > 0:
        initial_status = SubscriptionStatus.TRIAL
        trial_start = now
        trial_end = now + timedelta(days=trial_days)
        period_start = now
        period_end = trial_end
    else:
        initial_status = SubscriptionStatus.ACTIVE
        trial_start = None
        trial_end = None
        period_start = now
        period_end = compute_period_end(period_start, plan.billing_interval)

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status=initial_status,
        start_date=period_start,
        end_date=period_end,
        trial_start=trial_start,
        trial_end=trial_end,
        cancel_at_period_end=False
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Initialize first billing cycle
    cycle = BillingCycle(
        subscription_id=subscription.id,
        cycle_index=1,
        cycle_start_date=period_start,
        cycle_end_date=period_end,
        renewal_date=period_end if initial_status == SubscriptionStatus.TRIAL else period_start,
        status=BillingCycleStatus.PENDING
    )
    db.add(cycle)

    audit = AuditLog(
        entity_type="subscription",
        entity_id=subscription.id,
        action="subscription_created",
        old_value=None,
        new_value={"status": subscription.status.value, "plan": plan.name},
        performed_by="customer",
        customer_id=customer.id,
        subscription_id=subscription.id
    )
    db.add(audit)
    db.commit()
    db.refresh(subscription)

    return subscription

@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    status_filter: SubscriptionStatus = None,
    customer_id: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Subscription)
    if status_filter:
        query = query.filter(Subscription.status == status_filter)
    if customer_id:
        query = query.filter(Subscription.customer_id == customer_id)
    return query.order_by(Subscription.created_at.desc()).all()

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub

@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(subscription_id: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    try:
        updated = transition_subscription(
            db=db,
            subscription=sub,
            target_status=SubscriptionStatus.PAUSED,
            reason="User paused their subscription",
            actor="customer"
        )
        return updated
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(subscription_id: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    try:
        updated = transition_subscription(
            db=db,
            subscription=sub,
            target_status=SubscriptionStatus.ACTIVE,
            reason="User resumed paused subscription",
            actor="customer"
        )
        return updated
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    cancel_in: SubscriptionCancel,
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    if cancel_in.timing == CancellationTiming.END_OF_CYCLE:
        sub.cancel_at_period_end = True
        audit = AuditLog(
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            event_type="subscription.scheduled_cancellation",
            actor="customer",
            description=f"Subscription scheduled to cancel at end of period ({sub.current_period_end}). Reason: {cancel_in.reason}"
        )
        db.add(audit)
        db.commit()
        db.refresh(sub)
        return sub

    # Immediate cancellation
    try:
        updated = transition_subscription(
            db=db,
            subscription=sub,
            target_status=SubscriptionStatus.CANCELLED,
            reason=cancel_in.reason,
            actor="customer"
        )
        return updated
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/{subscription_id}/status", response_model=SubscriptionResponse)
def update_subscription_status(
    subscription_id: str,
    transition_in: SubscriptionStatusTransition,
    db: Session = Depends(get_db)
):
    """
    Task 4: Enforces valid subscription lifecycle transitions:
    - trial -> active, cancelled
    - active -> past_due, cancelled
    - past_due -> active, cancelled
    - Blocks all illegal transitions and records status timestamps.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    try:
        updated = transition_subscription(
            db=db,
            subscription=sub,
            target_status=transition_in.target_status,
            reason=transition_in.reason,
            actor="admin"
        )
        return updated
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
