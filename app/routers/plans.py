"""Plan management APIs."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PlanCreate, PlanOut, PlanUpdate
from app.services import plan_service

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("", response_model=PlanOut, status_code=201, summary="Create a plan")
def create_plan(payload: PlanCreate, db: Session = Depends(get_db)):
    return plan_service.create_plan(db, payload)


@router.get("", response_model=list[PlanOut], summary="List plans")
def list_plans(include_archived: bool = False, db: Session = Depends(get_db)):
    return plan_service.list_plans(db, include_archived)


@router.get("/{plan_id}", response_model=PlanOut, summary="Get one plan")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    return plan_service.get_plan(db, plan_id)


@router.patch("/{plan_id}", response_model=PlanOut, summary="Update a plan")
def update_plan(plan_id: int, payload: PlanUpdate, db: Session = Depends(get_db)):
    return plan_service.update_plan(db, plan_id, payload)


@router.post("/{plan_id}/archive", response_model=PlanOut, summary="Archive a plan")
def archive_plan(plan_id: int, db: Session = Depends(get_db)):
    return plan_service.archive_plan(db, plan_id)
