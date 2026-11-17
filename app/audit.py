"""Audit logging: every billing state change is written to the audit_logs table."""
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def _clean(value: Any) -> Any:
    """Make sure a value can be stored as JSON (datetimes and Decimals become strings)."""
    if value is None:
        return None
    return json.loads(json.dumps(value, default=str))


def log_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
    old_value: Any = None,
    new_value: Any = None,
    actor: str = "system",
) -> AuditLog:
    """Add an audit entry to the current transaction. The caller commits."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        customer_id=customer_id,
        subscription_id=subscription_id,
        old_value=_clean(old_value),
        new_value=_clean(new_value),
        actor=actor,
    )
    db.add(entry)
    return entry
