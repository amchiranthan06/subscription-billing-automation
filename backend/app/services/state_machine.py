from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.enums import SubscriptionStatus
from app.models.models import Subscription, AuditLog

class InvalidStateTransitionError(Exception):
    def __init__(self, current_status: SubscriptionStatus, target_status: SubscriptionStatus):
        super().__init__(
            f"Invalid subscription state transition: Cannot transition from '{current_status.value}' to '{target_status.value}'."
        )

# Graph of valid transitions
VALID_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
    SubscriptionStatus.TRIAL: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.ACTIVE: {
        SubscriptionStatus.PAST_DUE,
        SubscriptionStatus.PAUSED,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.PAST_DUE: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.PAUSED: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED
    },
    SubscriptionStatus.CANCELLED: set() # Terminal state
}

def can_transition(current: SubscriptionStatus, target: SubscriptionStatus) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())

def transition_subscription(
    db: Session,
    subscription: Subscription,
    target_status: SubscriptionStatus,
    reason: str,
    actor: str = "system"
) -> Subscription:
    """
    Executes a validated state transition on a subscription, updates relevant timestamps,
    and appends an immutable entry to the audit log.
    """
    if subscription.status == target_status:
        return subscription

    if not can_transition(subscription.status, target_status):
        raise InvalidStateTransitionError(subscription.status, target_status)

    now = datetime.now(timezone.utc)
    old_status = subscription.status
    
    # State update
    subscription.status = target_status
    subscription.updated_at = now

    # Timestamps update
    if target_status == SubscriptionStatus.CANCELLED:
        subscription.cancelled_at = now
    elif target_status == SubscriptionStatus.PAUSED:
        subscription.paused_at = now
    elif target_status == SubscriptionStatus.ACTIVE and old_status == SubscriptionStatus.PAUSED:
        subscription.paused_at = None

    # Audit Log creation
    audit_entry = AuditLog(
        customer_id=subscription.customer_id,
        subscription_id=subscription.id,
        event_type=f"subscription.state_changed.{target_status.value}",
        old_state={"status": old_status.value},
        new_state={"status": target_status.value},
        actor=actor,
        description=f"State transitioned from {old_status.value} to {target_status.value}. Reason: {reason}"
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(subscription)

    return subscription
