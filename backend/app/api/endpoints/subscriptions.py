from datetime import datetime, timezone, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Customer, Plan, Subscription, BillingCycle, AuditLog
from app.models.enums import (
    SubscriptionStatus, BillingInterval, BillingCycleStatus, CancellationTiming
)
from app.schemas.schemas import (
    SubscriptionCreate, SubscriptionResponse, SubscriptionCancel, SubscriptionStatusTransition,
    SubscriptionChangePlan, ProrationPreviewRequest, ProrationPreviewResponse, PlanChangeHistoryItem
)
from app.services.state_machine import transition_subscription, InvalidStateTransitionError
from app.services.proration import preview_plan_change, apply_plan_change_with_proration

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

@router.post("/{subscription_id}/proration-preview", response_model=ProrationPreviewResponse)
def get_proration_preview(
    subscription_id: str,
    payload: ProrationPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Milestone 2 - Task 2: Live preview of mid-cycle proration adjustment
    before confirming the upgrade/downgrade.
    Computes remaining days, unused old plan credit, new plan charge, and net amount due.
    """
    try:
        preview = preview_plan_change(
            db=db,
            subscription_id=subscription_id,
            new_plan_id=payload.new_plan_id
        )
        return preview
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/change-plan", response_model=SubscriptionResponse)
def change_subscription_plan(
    subscription_id: str,
    plan_in: SubscriptionChangePlan,
    db: Session = Depends(get_db)
):
    """
    Milestone 2 - Task 2: Upgrade or downgrade a subscription to a new active plan.
    - Validates target plan exists and is active.
    - Prevents changing to the same plan or changing cancelled subscriptions.
    - Computes mid-cycle proration (unused old plan credit, new plan charge).
    - Automatically generates an itemized adjustment invoice (PRORATION_CREDIT / PRORATION_DEBIT).
    - Updates subscription with the new plan.
    - Records immutable audit log with full financial details.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    if sub.status == SubscriptionStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change plan of a cancelled subscription")

    new_plan = db.query(Plan).filter(Plan.id == plan_in.new_plan_id).first()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target plan not found")

    if not new_plan.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot switch to an inactive or archived plan")

    if new_plan.id == sub.plan_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription is already on this plan")

    try:
        apply_plan_change_with_proration(
            db=db,
            subscription_id=subscription_id,
            new_plan_id=plan_in.new_plan_id
        )
        db.refresh(sub)
        return sub
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{subscription_id}/plan-history", response_model=list[PlanChangeHistoryItem])
def get_subscription_plan_history(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """
    Milestone 2 - Task 2: Retrieve historical plan change timeline for a subscription.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.subscription_id == subscription_id, AuditLog.action == "plan_changed")
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    history = []
    for log in logs:
        old_val = log.old_value or {}
        new_val = log.new_value or {}
        history.append({
            "date": log.created_at,
            "from_plan": old_val.get("plan_name", "Previous Plan"),
            "to_plan": new_val.get("plan_name", "New Plan"),
            "unused_credit": Decimal(str(new_val.get("unused_credit", 0.00))),
            "new_charge": Decimal(str(new_val.get("new_charge", 0.00))),
            "net_adjustment": Decimal(str(new_val.get("net_amount_due", 0.00))),
            "invoice_number": new_val.get("invoice_number")
        })

    return history

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
            entity_type="subscription",
            entity_id=sub.id,
            action="subscription_cancelled",
            old_value={"cancel_at_period_end": False, "status": sub.status.value},
            new_value={"cancel_at_period_end": True, "timing": "end_of_cycle", "end_date": sub.end_date.isoformat(), "reason": cancel_in.reason},
            performed_by="customer",
            customer_id=sub.customer_id,
            subscription_id=sub.id
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
