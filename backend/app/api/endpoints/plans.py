from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Plan, Subscription, AuditLog
from app.models.enums import SubscriptionStatus
from app.schemas.schemas import PlanCreate, PlanUpdate, PlanResponse

router = APIRouter(prefix="/plans", tags=["Plan Management APIs (Task 5)"])

# 1. CREATE PLAN: POST /plans
@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(plan_in: PlanCreate, db: Session = Depends(get_db)):
    """Creates a new subscription pricing plan."""
    plan_code = (plan_in.code or plan_in.name.lower().replace(" ", "_")).strip()
    
    existing = db.query(Plan).filter(Plan.code == plan_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with code '{plan_code}' already exists."
        )
    
    plan = Plan(
        name=plan_in.name,
        code=plan_code,
        description=plan_in.description,
        price=plan_in.price,
        currency=plan_in.currency,
        billing_interval=plan_in.billing_interval,
        trial_days=plan_in.trial_days,
        features=plan_in.features or {},
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    audit = AuditLog(
        entity_type="plan",
        entity_id=plan.id,
        action="plan_created",
        old_value=None,
        new_value={"code": plan.code, "price": str(plan.price), "name": plan.name},
        performed_by="admin"
    )
    db.add(audit)
    db.commit()

    return plan

# 2. LIST PLANS: GET /plans
@router.get("", response_model=list[PlanResponse])
def list_plans(active_only: bool = False, db: Session = Depends(get_db)):
    """Retrieves all subscription plans, with optional active_only filter."""
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.is_active.is_(True))
    return query.order_by(Plan.price.asc()).all()

# GET SINGLE PLAN: GET /plans/{id}
@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Retrieves a single plan by its ID."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan

# 3. UPDATE PLAN: PUT /plans/{id}
@router.put("/{plan_id}", response_model=PlanResponse)
@router.patch("/{plan_id}", response_model=PlanResponse, include_in_schema=False)
def update_plan(plan_id: str, plan_update: PlanUpdate, db: Session = Depends(get_db)):
    """Updates an existing subscription plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    old_data = {
        "name": plan.name,
        "price": str(plan.price),
        "trial_days": plan.trial_days,
        "is_active": plan.is_active
    }

    update_data = plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    audit = AuditLog(
        entity_type="plan",
        entity_id=plan.id,
        action="plan_updated",
        old_value=old_data,
        new_value={
            "name": plan.name,
            "price": str(plan.price),
            "trial_days": plan.trial_days,
            "is_active": plan.is_active
        },
        performed_by="admin"
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)
    return plan

# 4. ARCHIVE PLAN: PATCH /plans/{id}/archive
@router.patch("/{plan_id}/archive", response_model=PlanResponse)
@router.post("/{plan_id}/archive", response_model=PlanResponse, include_in_schema=False)
def archive_plan(plan_id: str, db: Session = Depends(get_db)):
    """Archives a plan by setting is_active = False so new users cannot subscribe."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    plan.is_active = False
    audit = AuditLog(
        entity_type="plan",
        entity_id=plan.id,
        action="plan_archived",
        old_value={"is_active": True},
        new_value={"is_active": False},
        performed_by="admin"
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)
    return plan

# 5. DELETE PLAN: DELETE /plans/{id}
@router.delete("/{plan_id}")
def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    """Deletes a plan. Rejects deletion if active subscriptions are using this plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Check for active subscriptions using this plan
    active_subs_count = db.query(Subscription).filter(
        Subscription.plan_id == plan_id,
        Subscription.status.in_([SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE])
    ).count()

    if active_subs_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete plan '{plan.name}' because {active_subs_count} active subscription(s) are using it. Please archive it instead."
        )

    plan_name = plan.name
    db.delete(plan)

    audit = AuditLog(
        entity_type="plan",
        entity_id=plan_id,
        action="plan_deleted",
        old_value={"name": plan_name},
        new_value=None,
        performed_by="admin"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Plan '{plan_name}' (ID: {plan_id}) was deleted successfully."}
