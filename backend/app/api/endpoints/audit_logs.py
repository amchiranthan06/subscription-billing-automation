from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    customer_id: str = None,
    subscription_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if customer_id:
        query = query.filter(AuditLog.customer_id == customer_id)
    if subscription_id:
        query = query.filter(AuditLog.subscription_id == subscription_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
