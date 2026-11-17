import pytest

from app.enums import SubscriptionStatus as S
from app.models import Subscription
from app.state_machine import InvalidTransitionError, can_transition, move_to
from app.utils import utcnow

VALID = [
    (S.TRIAL, S.ACTIVE),
    (S.TRIAL, S.CANCELLED),
    (S.ACTIVE, S.PAST_DUE),
    (S.ACTIVE, S.CANCELLED),
    (S.PAST_DUE, S.CANCELLED),
    (S.PAST_DUE, S.ACTIVE),
]

INVALID = [
    (S.TRIAL, S.PAST_DUE),
    (S.TRIAL, S.TRIAL),
    (S.ACTIVE, S.TRIAL),
    (S.ACTIVE, S.ACTIVE),
    (S.PAST_DUE, S.TRIAL),
    (S.CANCELLED, S.TRIAL),
    (S.CANCELLED, S.ACTIVE),
    (S.CANCELLED, S.PAST_DUE),
]


@pytest.mark.parametrize("current,target", VALID)
def test_valid_transitions(current, target):
    assert can_transition(current, target)


@pytest.mark.parametrize("current,target", INVALID)
def test_invalid_transitions(current, target):
    assert not can_transition(current, target)


def test_move_to_sets_timestamps():
    sub = Subscription(status=S.TRIAL)
    now = utcnow()

    move_to(sub, S.ACTIVE, now)
    assert sub.status == S.ACTIVE
    assert sub.activated_at == now
    assert sub.status_changed_at == now

    move_to(sub, S.PAST_DUE, now)
    assert sub.past_due_at == now

    move_to(sub, S.CANCELLED, now)
    assert sub.cancelled_at == now


def test_invalid_move_raises_and_changes_nothing():
    sub = Subscription(status=S.CANCELLED)
    with pytest.raises(InvalidTransitionError):
        move_to(sub, S.ACTIVE, utcnow())
    assert sub.status == S.CANCELLED
