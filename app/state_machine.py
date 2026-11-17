"""Subscription state machine.

Valid status changes:
    trial     -> active, cancelled
    active    -> past_due, cancelled
    past_due  -> active (payment recovered), cancelled
    cancelled -> (final, nothing allowed)

Every change records a timestamp on the subscription (status_changed_at plus
activated_at / past_due_at / cancelled_at). The full history is in audit_logs.
"""
from datetime import datetime

from app.enums import SubscriptionStatus as S
from app.errors import ConflictError

ALLOWED_TRANSITIONS = {
    S.TRIAL: {S.ACTIVE, S.CANCELLED},
    S.ACTIVE: {S.PAST_DUE, S.CANCELLED},
    S.PAST_DUE: {S.ACTIVE, S.CANCELLED},
    S.CANCELLED: set(),
}


class InvalidTransitionError(ConflictError):
    def __init__(self, current: S, target: S):
        super().__init__(f"Invalid status change: {current.value} -> {target.value}")


def can_transition(current: S, target: S) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def assert_transition(current: S, target: S) -> None:
    if not can_transition(current, target):
        raise InvalidTransitionError(current, target)


def move_to(sub, new_status: S, now: datetime) -> None:
    """Validate the change, then set the new status and its timestamps on the subscription."""
    assert_transition(sub.status, new_status)
    sub.status = new_status
    sub.status_changed_at = now
    if new_status == S.ACTIVE and sub.activated_at is None:
        sub.activated_at = now
    elif new_status == S.PAST_DUE:
        sub.past_due_at = now
    elif new_status == S.CANCELLED:
        sub.cancelled_at = now
