"""Customer subscription APIs: create, change plan, pause, resume, cancel."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import SubscriptionStatus
from app.schemas import (
    CancelRequest,
    ChangePlanRequest,
    SubscriptionCreate,
    SubscriptionOut,
    TransitionRequest,
)
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionOut, status_code=201, summary="Create a subscription (with trial)")
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    return subscription_service.create_subscription(
        db, payload.customer_id, payload.plan_id, payload.start_trial
    )


@router.get("", response_model=list[SubscriptionOut], summary="List subscriptions")
def list_subscriptions(
    customer_id: Optional[int] = None,
    status: Optional[SubscriptionStatus] = None,
    db: Session = Depends(get_db),
):
    return subscription_service.list_subscriptions(db, customer_id, status)


@router.get("/{subscription_id}", response_model=SubscriptionOut, summary="Get one subscription")
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    return subscription_service.get_subscription(db, subscription_id)


@router.post("/{subscription_id}/change-plan", response_model=SubscriptionOut, summary="Change plan")
def change_plan(subscription_id: int, payload: ChangePlanRequest, db: Session = Depends(get_db)):
    return subscription_service.change_plan(db, subscription_id, payload.new_plan_id, payload.effective)


@router.post("/{subscription_id}/pause", response_model=SubscriptionOut, summary="Pause a subscription")
def pause_subscription(subscription_id: int, db: Session = Depends(get_db)):
    return subscription_service.pause_subscription(db, subscription_id)


@router.post("/{subscription_id}/resume", response_model=SubscriptionOut, summary="Resume a subscription")
def resume_subscription(subscription_id: int, db: Session = Depends(get_db)):
    return subscription_service.resume_subscription(db, subscription_id)


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionOut,
    summary="Cancel (immediately or at end of cycle)",
)
def cancel_subscription(subscription_id: int, payload: CancelRequest, db: Session = Depends(get_db)):
    return subscription_service.cancel_subscription(db, subscription_id, payload.timing, payload.reason)


@router.post(
    "/{subscription_id}/transition",
    response_model=SubscriptionOut,
    summary="Admin/testing: request a status change (state machine enforced)",
)
def transition_subscription(subscription_id: int, payload: TransitionRequest, db: Session = Depends(get_db)):
    return subscription_service.transition_subscription(
        db, subscription_id, payload.to_status, payload.reason
    )
