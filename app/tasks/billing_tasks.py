"""Celery tasks for the billing cycle scheduler."""
import logging
from dataclasses import asdict

from app.audit import log_event
from app.database import SessionLocal
from app.models import BillingCycle, Subscription
from app.services.scheduler_service import run_billing_scan
from app.tasks.celery_app import celery_app
from app.utils import utcnow

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.billing_tasks.generate_invoice_job")
def generate_invoice_job(billing_cycle_id: int) -> dict:
    """Invoice generation job for one billing cycle.

    Milestone 1 scope: the scheduler triggers this job at the correct renewal date, and the
    job confirms it received the cycle and records that in the audit log.
    TODO (Milestone 2): build the invoice here (line items, proration, tax, invoice number).
    """
    with SessionLocal() as db:
        cycle = db.get(BillingCycle, billing_cycle_id)
        if cycle is None:
            logger.warning("Invoice job received unknown billing cycle %s", billing_cycle_id)
            return {"billing_cycle_id": billing_cycle_id, "status": "not_found"}

        sub = db.get(Subscription, cycle.subscription_id)
        log_event(
            db,
            action="billing_cycle.invoice_job_received",
            entity_type="billing_cycle",
            entity_id=cycle.id,
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            new_value={"cycle_number": cycle.cycle_number, "note": "invoice engine arrives in Milestone 2"},
        )
        db.commit()
        logger.info(
            "Invoice job received: subscription %s, cycle %s (%s to %s)",
            sub.id, cycle.cycle_number, cycle.period_start, cycle.period_end,
        )
    return {"billing_cycle_id": billing_cycle_id, "status": "received"}


@celery_app.task(name="app.tasks.billing_tasks.scan_billing_cycles")
def scan_billing_cycles() -> dict:
    """Runs on the Celery beat schedule: find due subscriptions and trigger invoice jobs."""
    with SessionLocal() as db:
        result = run_billing_scan(
            db,
            now=utcnow(),
            dispatch=lambda billing_cycle_id: generate_invoice_job.delay(billing_cycle_id),
        )
    summary = asdict(result)
    summary["as_of"] = result.as_of.isoformat()
    logger.info("Billing scan finished: %s", summary)
    return summary
