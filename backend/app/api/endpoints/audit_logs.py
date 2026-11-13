from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logging (Task 10)"])

@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Task 10 Deliverable:
    View and filter automatically generated audit trail entries.
    Supported event actions:
    - plan_created
    - plan_updated
    - customer_created
    - subscription_created
    - plan_changed
    - subscription_cancelled
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if customer_id:
        query = query.filter(AuditLog.customer_id == customer_id)
    if subscription_id:
        query = query.filter(AuditLog.subscription_id == subscription_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
