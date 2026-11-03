from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Plan, AuditLog
from app.schemas.schemas import PlanCreate, PlanUpdate, PlanResponse

router = APIRouter(prefix="/plans", tags=["Plans"])

@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(plan_in: PlanCreate, db: Session = Depends(get_db)):
    existing = db.query(Plan).filter(Plan.code == plan_in.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with code '{plan_in.code}' already exists."
        )
    
    plan = Plan(
        name=plan_in.name,
        code=plan_in.code.lower(),
        description=plan_in.description,
        price=plan_in.price,
        currency=plan_in.currency,
        billing_interval=plan_in.billing_interval,
        trial_days=plan_in.trial_days,
        feature_entitlements=plan_in.feature_entitlements or {},
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    audit = AuditLog(
        event_type="plan.created",
        new_state={"code": plan.code, "price": str(plan.price)},
        actor="admin",
        description=f"Plan '{plan.name}' created with price {plan.price} {plan.currency}"
    )
    db.add(audit)
    db.commit()

    return plan

@router.get("", response_model=list[PlanResponse])
def list_plans(active_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.is_active.is_(True))
    return query.order_by(Plan.price.asc()).all()

@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan

@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: str, plan_update: PlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    old_price = str(plan.price)
    update_data = plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    audit = AuditLog(
        event_type="plan.updated",
        old_state={"price": old_price},
        new_state={"price": str(plan.price), "is_active": plan.is_active},
        actor="admin",
        description=f"Plan '{plan.name}' updated."
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)
    return plan

@router.post("/{plan_id}/archive", response_model=PlanResponse)
def archive_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    plan.is_active = False
    audit = AuditLog(
        event_type="plan.archived",
        actor="admin",
        description=f"Plan '{plan.name}' was archived."
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)
    return plan
