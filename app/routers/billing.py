"""Billing cycle engine controls, billing cycle list and audit log list."""
from datetime import timezone
from typing import Callable, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import BillingCycleStatus
from app.models import AuditLog, BillingCycle
from app.schemas import AuditLogOut, BillingCycleOut, ScanRequest, ScanResultOut
from app.services.scheduler_service import run_billing_scan
from app.utils import utcnow

router = APIRouter(tags=["Billing cycles & audit log"])


def get_dispatcher() -> Callable[[int], None]:
    """Returns the function that sends an invoice job to Celery. Tests replace this."""
    from app.tasks.billing_tasks import generate_invoice_job  # imported here so the API starts without Celery

    return lambda billing_cycle_id: generate_invoice_job.delay(billing_cycle_id)


@router.post(
    "/billing/run-scan",
    response_model=ScanResultOut,
    summary="Run the billing scan now (same logic Celery beat runs on a schedule)",
)
def run_scan(
    payload: Optional[ScanRequest] = None,
    db: Session = Depends(get_db),
    dispatch: Callable[[int], None] = Depends(get_dispatcher),
):
    as_of = payload.as_of if payload and payload.as_of else utcnow()
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    result = run_billing_scan(db, as_of, dispatch)
    return {
        "as_of": result.as_of,
        "trials_converted": result.trials_converted,
        "renewals_created": result.renewals_created,
        "cancellations_applied": result.cancellations_applied,
        "invoice_jobs_dispatched": result.invoice_jobs_dispatched,
        "errors": result.errors,
    }


@router.get("/billing/cycles", response_model=list[BillingCycleOut], summary="List billing cycles")
def list_cycles(
    subscription_id: Optional[int] = None,
    status: Optional[BillingCycleStatus] = None,
    db: Session = Depends(get_db),
):
    stmt = select(BillingCycle).order_by(BillingCycle.id)
    if subscription_id is not None:
        stmt = stmt.where(BillingCycle.subscription_id == subscription_id)
    if status is not None:
        stmt = stmt.where(BillingCycle.status == status)
    return list(db.scalars(stmt).all())


@router.get("/audit-logs", response_model=list[AuditLogOut], summary="List audit log entries (newest first)")
def list_audit_logs(
    customer_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if customer_id is not None:
        stmt = stmt.where(AuditLog.customer_id == customer_id)
    if subscription_id is not None:
        stmt = stmt.where(AuditLog.subscription_id == subscription_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    return list(db.scalars(stmt).all())
