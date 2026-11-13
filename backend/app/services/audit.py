from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog

def create_audit_log(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
    performed_by: str = "system",
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> AuditLog:
    """
    Task 10: Centralized audit logging engine.
    Automatically generates immutable audit records for all critical billing events:
    - plan_created
    - plan_updated
    - customer_created
    - subscription_created
    - plan_changed
    - subscription_cancelled
    """
    audit = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by,
        customer_id=customer_id,
        subscription_id=subscription_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
