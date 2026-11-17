"""Plan management: create, update, archive, list."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import log_event
from app.enums import PlanStatus
from app.errors import BadRequestError, ConflictError, NotFoundError
from app.models import Plan
from app.schemas import PlanCreate, PlanUpdate
from app.utils import utcnow

_NOT_NULLABLE = ("name", "price", "trial_period_days", "features")


def get_plan(db: Session, plan_id: int) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NotFoundError(f"Plan {plan_id} not found")
    return plan


def list_plans(db: Session, include_archived: bool = False) -> list[Plan]:
    stmt = select(Plan).order_by(Plan.id)
    if not include_archived:
        stmt = stmt.where(Plan.status == PlanStatus.ACTIVE)
    return list(db.scalars(stmt).all())


def _snapshot(plan: Plan) -> dict:
    return {
        "name": plan.name,
        "price": plan.price,
        "currency": plan.currency,
        "billing_interval": plan.billing_interval.value,
        "trial_period_days": plan.trial_period_days,
        "features": plan.features,
    }


def _name_taken(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    stmt = select(Plan.id).where(Plan.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Plan.id != exclude_id)
    return db.scalar(stmt) is not None


def create_plan(db: Session, data: PlanCreate) -> Plan:
    if _name_taken(db, data.name):
        raise ConflictError(f"A plan named '{data.name}' already exists")

    plan = Plan(
        name=data.name,
        description=data.description,
        price=data.price,
        currency=data.currency,
        billing_interval=data.billing_interval,
        trial_period_days=data.trial_period_days,
        features=data.features,
        status=PlanStatus.ACTIVE,
    )
    db.add(plan)
    db.flush()
    log_event(db, action="plan.created", entity_type="plan", entity_id=plan.id, new_value=_snapshot(plan))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"A plan named '{data.name}' already exists")
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan_id: int, data: PlanUpdate) -> Plan:
    plan = get_plan(db, plan_id)
    if plan.status == PlanStatus.ARCHIVED:
        raise ConflictError("Archived plans cannot be edited")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise BadRequestError("No fields to update were provided")
    for field in _NOT_NULLABLE:
        if field in changes and changes[field] is None:
            raise BadRequestError(f"'{field}' cannot be null")
    if "name" in changes and _name_taken(db, changes["name"], exclude_id=plan.id):
        raise ConflictError(f"A plan named '{changes['name']}' already exists")

    old_values = {field: getattr(plan, field) for field in changes}
    for field, value in changes.items():
        setattr(plan, field, value)
    log_event(
        db,
        action="plan.updated",
        entity_type="plan",
        entity_id=plan.id,
        old_value=old_values,
        new_value=changes,
    )
    db.commit()
    db.refresh(plan)
    return plan


def archive_plan(db: Session, plan_id: int) -> Plan:
    """Archived plans cannot get new subscribers. Existing subscribers keep their plan."""
    plan = get_plan(db, plan_id)
    if plan.status == PlanStatus.ARCHIVED:
        raise ConflictError("Plan is already archived")
    plan.status = PlanStatus.ARCHIVED
    plan.archived_at = utcnow()
    log_event(
        db,
        action="plan.archived",
        entity_type="plan",
        entity_id=plan.id,
        old_value={"status": "active"},
        new_value={"status": "archived"},
    )
    db.commit()
    db.refresh(plan)
    return plan
