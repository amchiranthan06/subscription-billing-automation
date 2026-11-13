from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import BillingCycle, Subscription
from app.schemas.schemas import BillingCycleResponse
from app.services.billing_cycle import (
    generate_billing_cycle,
    get_billing_cycle_history
)

router = APIRouter(prefix="/billing-cycles", tags=["Billing Cycle Engine (Task 9)"])

@router.post("/generate/{subscription_id}", response_model=BillingCycleResponse, status_code=status.HTTP_201_CREATED)
def trigger_billing_cycle(subscription_id: str, db: Session = Depends(get_db)):
    """
    Task 9 Deliverable:
    Triggers the Billing Cycle Engine to calculate the next renewal date
    (monthly or annual) and store sequential cycle history.
    """
    return generate_billing_cycle(db=db, subscription_id=subscription_id)

@router.get("/subscription/{subscription_id}", response_model=list[BillingCycleResponse])
def list_subscription_billing_cycles(subscription_id: str, db: Session = Depends(get_db)):
    """
    Task 9 Deliverable:
    Retrieves full historical billing cycle records for a subscription.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID '{subscription_id}' not found."
        )
    return get_billing_cycle_history(db=db, subscription_id=subscription_id)

@router.get("/{cycle_id}", response_model=BillingCycleResponse)
def get_billing_cycle(cycle_id: str, db: Session = Depends(get_db)):
    """Retrieves a single billing cycle record by ID."""
    cycle = db.query(BillingCycle).filter(BillingCycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Billing cycle with ID '{cycle_id}' not found."
        )
    return cycle
