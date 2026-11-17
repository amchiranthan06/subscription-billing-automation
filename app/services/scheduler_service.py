"""Billing cycle engine: finds subscriptions that are due and triggers invoice jobs.

run_billing_scan() does three things, in order:
  1. Trials whose end date has passed  -> trial becomes active (or cancelled if cancellation
     was scheduled) and the first billing cycle is created.
  2. Active subscriptions whose period has ended -> a new billing cycle is created and the
     period moves forward (or the subscription is cancelled if cancellation was scheduled).
     Paused subscriptions are skipped.
  3. Billing cycles that have no invoice job yet -> an invoice-generation job is sent
     through `dispatch` (a Celery task in production).

It is safe to run repeatedly: a cycle is only ever created once per period and only
dispatched once.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import log_event
from app.enums import BillingCycleStatus, SubscriptionStatus
from app.models import BillingCycle, Subscription
from app.services.billing_cycle_service import start_billing_period
from app.services.subscription_service import apply_pending_plan, apply_transition

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    as_of: datetime
    trials_converted: int = 0
    renewals_created: int = 0
    cancellations_applied: int = 0
    invoice_jobs_dispatched: int = 0
    errors: int = 0


def run_billing_scan(db: Session, now: datetime, dispatch: Callable[[int], None]) -> ScanResult:
    result = ScanResult(as_of=now)
    _convert_ended_trials(db, now, result)
    _process_renewals(db, now, result)
    _dispatch_invoice_jobs(db, now, dispatch, result)
    return result


def _convert_ended_trials(db: Session, now: datetime, result: ScanResult) -> None:
    ids = db.scalars(
        select(Subscription.id)
        .where(Subscription.status == SubscriptionStatus.TRIAL, Subscription.trial_end <= now)
        .order_by(Subscription.id)
    ).all()

    for sub_id in ids:
        try:
            sub = db.get(Subscription, sub_id, with_for_update=True)
            if (
                sub is None
                or sub.status != SubscriptionStatus.TRIAL
                or sub.trial_end is None
                or sub.trial_end > now
            ):
                db.rollback()
                continue

            cancelled = sub.cancel_at_period_end
            if cancelled:
                apply_transition(
                    db, sub, SubscriptionStatus.CANCELLED, now=now,
                    reason="Trial ended and cancellation was scheduled",
                )
            else:
                apply_transition(
                    db, sub, SubscriptionStatus.ACTIVE, now=now,
                    reason="Trial period ended", period_start=sub.trial_end,
                )
            db.commit()

            if cancelled:
                result.cancellations_applied += 1
            else:
                result.trials_converted += 1
        except Exception:
            db.rollback()
            logger.exception("Could not process trial subscription %s", sub_id)
            result.errors += 1


def _process_renewals(db: Session, now: datetime, result: ScanResult) -> None:
    ids = db.scalars(
        select(Subscription.id)
        .where(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]),
            Subscription.is_paused.is_(False),
            Subscription.current_period_end <= now,
        )
        .order_by(Subscription.id)
    ).all()

    for sub_id in ids:
        try:
            sub = db.get(Subscription, sub_id, with_for_update=True)
            if (
                sub is None
                or sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE)
                or sub.is_paused
                or sub.current_period_end is None
                or sub.current_period_end > now
            ):
                db.rollback()
                continue

            if sub.cancel_at_period_end:
                apply_transition(
                    db, sub, SubscriptionStatus.CANCELLED, now=now,
                    reason="Billing period ended and cancellation was scheduled",
                )
                db.commit()
                result.cancellations_applied += 1
            elif sub.status == SubscriptionStatus.ACTIVE:
                apply_pending_plan(db, sub)
                start_billing_period(db, sub, period_start=sub.current_period_end)
                db.commit()
                result.renewals_created += 1
            else:
                # past_due: payment problems are handled by the retry engine (later milestone)
                db.rollback()
        except Exception:
            db.rollback()
            logger.exception("Could not process renewal for subscription %s", sub_id)
            result.errors += 1


def _dispatch_invoice_jobs(
    db: Session, now: datetime, dispatch: Callable[[int], None], result: ScanResult
) -> None:
    ids = db.scalars(
        select(BillingCycle.id)
        .where(
            BillingCycle.status == BillingCycleStatus.PENDING,
            BillingCycle.invoice_job_triggered_at.is_(None),
        )
        .order_by(BillingCycle.id)
    ).all()

    for cycle_id in ids:
        try:
            dispatch(cycle_id)
        except Exception:
            # e.g. the message broker (Redis) is down. Leave the cycle untouched so the
            # next scan tries again, and stop for now.
            logger.exception("Could not dispatch invoice job for billing cycle %s", cycle_id)
            result.errors += 1
            break

        cycle = db.get(BillingCycle, cycle_id)
        cycle.invoice_job_triggered_at = now
        sub = db.get(Subscription, cycle.subscription_id)
        log_event(
            db,
            action="billing_cycle.invoice_job_triggered",
            entity_type="billing_cycle",
            entity_id=cycle.id,
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            new_value={"cycle_number": cycle.cycle_number, "period_start": cycle.period_start},
        )
        db.commit()
        result.invoice_jobs_dispatched += 1
