from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.enums import SubscriptionStatus
from app.models.models import Subscription, AuditLog

class InvalidStateTransitionError(Exception):
    def __init__(self, current_status: SubscriptionStatus, target_status: SubscriptionStatus):
        allowed = [s.value for s in VALID_TRANSITIONS.get(current_status, set())]
        allowed_str = ", ".join(allowed) if allowed else "None (Terminal State)"
        super().__init__(
            f"Invalid subscription state transition: Cannot transition from '{current_status.value}' to '{target_status.value}'. "
            f"Allowed transitions from '{current_status.value}' are: [{allowed_str}]."
        )

# ----------------- TASK 4: STATE TRANSITION MATRIX -----------------
# Allowed States: trial, active, past_due, cancelled
# Valid Transitions:
# trial    -> active, cancelled
# active   -> past_due, cancelled (and paused)
# past_due -> active, cancelled
# cancelled -> (Terminal State: No transitions allowed)
VALID_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
    SubscriptionStatus.TRIAL: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.ACTIVE: {
        SubscriptionStatus.PAST_DUE,
        SubscriptionStatus.CANCELLED,
        SubscriptionStatus.PAUSED # Supported for Task 8 Pause
    },
    SubscriptionStatus.PAST_DUE: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.PAUSED: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.CANCELLED: set() # Terminal State: No transitions permitted
}

def can_transition(current: SubscriptionStatus, target: SubscriptionStatus) -> bool:
    """Checks whether the state transition is valid according to the matrix."""
    return target in VALID_TRANSITIONS.get(current, set())

def transition_subscription(
    db: Session,
    subscription: Subscription,
    target_status: SubscriptionStatus,
    reason: str = "State transition requested",
    actor: str = "system"
) -> Subscription:
    """
    Executes a validated state transition on a subscription.
    1. Validates the transition against the allowed matrix.
    2. Updates subscription status and timestamps (updated_at, cancelled_at).
    3. Records an immutable audit log entry.
    """
    if subscription.status == target_status:
        return subscription

    if not can_transition(subscription.status, target_status):
        raise InvalidStateTransitionError(subscription.status, target_status)

    now = datetime.now(timezone.utc)
    old_status = subscription.status
    
    # Update status and timestamps
    subscription.status = target_status
    subscription.updated_at = now

    if target_status == SubscriptionStatus.CANCELLED:
        subscription.cancelled_at = now
    elif target_status == SubscriptionStatus.PAUSED:
        subscription.paused_at = now
    elif target_status == SubscriptionStatus.ACTIVE and old_status == SubscriptionStatus.PAUSED:
        subscription.paused_at = None

    # Determine action name (Task 10: subscription_cancelled)
    if target_status == SubscriptionStatus.CANCELLED:
        action_name = "subscription_cancelled"
    else:
        action_name = f"state_transition_from_{old_status.value}_to_{target_status.value}"

    # Record immutable audit log entry
    audit_entry = AuditLog(
        entity_type="subscription",
        entity_id=subscription.id,
        action=action_name,
        old_value={"status": old_status.value},
        new_value={
            "status": target_status.value,
            "transitioned_at": now.isoformat(),
            "reason": reason
        },
        performed_by=actor,
        customer_id=subscription.customer_id,
        subscription_id=subscription.id
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(subscription)

    return subscription
