import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Payment, Invoice, Subscription, Customer
from app.models.enums import PaymentStatus, InvoiceStatus, SubscriptionStatus
from app.services.audit import create_audit_log
from app.services.state_machine import transition_subscription, InvalidStateTransitionError


def generate_unique_payment_reference(db: Session) -> str:
    """
    Generates a unique transaction identifier in format: TXN-YYYYMMDD-XXXXX
    e.g. TXN-20261120-74892
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")

    while True:
        rand_suffix = f"{random.randint(10000, 99999)}"
        ref = f"TXN-{date_part}-{rand_suffix}"
        existing = db.query(Payment).filter(Payment.payment_reference == ref).first()
        if not existing:
            return ref


def handle_payment_webhook(
    db: Session,
    event: str,
    invoice_id: str,
    payment_reference: Optional[str] = None,
    amount: Optional[Decimal] = None,
    failure_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes incoming payment webhook events:
    - 'payment_success':
        • Invoice: unpaid -> paid, paid_at = now
        • Subscription: remains active (or transitions trial/past_due -> active)
        • Audit log: 'payment_success'
    - 'payment_failed':
        • Invoice: remains unpaid (or failed)
        • Subscription: active -> past_due
        • Audit log: 'payment_failed'
    - 'payment_refunded':
        • Invoice: paid -> void
        • Payment: success -> refunded
        • Audit log: 'payment_refunded'
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice '{invoice_id}' not found.")

    subscription = invoice.subscription
    now = datetime.now(timezone.utc)

    # Find associated payment if reference provided or latest payment for this invoice
    payment = None
    if payment_reference:
        payment = db.query(Payment).filter(Payment.payment_reference == payment_reference).first()
    if not payment:
        payment = (
            db.query(Payment)
            .filter(Payment.invoice_id == invoice.id)
            .order_by(Payment.created_at.desc())
            .first()
        )

    clean_event = event.strip().lower()

    if clean_event == "payment_success":
        # 1. Update Invoice
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = now
        invoice.updated_at = now

        # 2. Update Payment record if present
        if payment:
            payment.status = PaymentStatus.SUCCESS
            payment.payment_date = now
            payment.updated_at = now

        # 3. Update Subscription lifecycle if needed
        sub_status_before = subscription.status.value if subscription else "none"
        if subscription and subscription.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.PAST_DUE]:
            try:
                transition_subscription(
                    db=db,
                    subscription=subscription,
                    target_status=SubscriptionStatus.ACTIVE,
                    reason="Payment succeeded via mock gateway webhook"
                )
            except InvalidStateTransitionError:
                # Direct safe update if transition path is bypassed
                subscription.status = SubscriptionStatus.ACTIVE

        db.commit()
        db.refresh(invoice)

        # 4. Audit Log
        create_audit_log(
            db=db,
            entity_type="payment",
            entity_id=payment.id if payment else invoice.id,
            action="payment_success",
            old_value={"invoice_status": "unpaid", "subscription_status": sub_status_before},
            new_value={
                "invoice_number": invoice.invoice_number,
                "amount": float(invoice.total_amount),
                "transaction_id": payment.payment_reference if payment else None,
                "status": "paid",
                "subscription_status": subscription.status.value if subscription else None
            },
            performed_by="payment_gateway_webhook",
            customer_id=invoice.customer_id,
            subscription_id=invoice.subscription_id
        )

        return {
            "status": "processed",
            "event": "payment_success",
            "invoice_number": invoice.invoice_number,
            "invoice_status": invoice.status.value,
            "subscription_status": subscription.status.value if subscription else None,
            "transaction_id": payment.payment_reference if payment else None,
            "message": "Invoice marked as paid and subscription is active."
        }

    elif clean_event == "payment_failed":
        # 1. Payment failed
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = failure_reason or "Card declined by issuing bank (mock)"
            payment.retry_count = (payment.retry_count or 0) + 1
            payment.updated_at = now

        # 2. Subscription transition active -> past_due
        sub_status_before = subscription.status.value if subscription else "none"
        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            try:
                transition_subscription(
                    db=db,
                    subscription=subscription,
                    target_status=SubscriptionStatus.PAST_DUE,
                    reason="Payment transaction failed via mock gateway webhook"
                )
            except InvalidStateTransitionError:
                subscription.status = SubscriptionStatus.PAST_DUE

        db.commit()

        # 3. Audit Log
        create_audit_log(
            db=db,
            entity_type="payment",
            entity_id=payment.id if payment else invoice.id,
            action="payment_failed",
            old_value={"subscription_status": sub_status_before},
            new_value={
                "invoice_number": invoice.invoice_number,
                "reason": failure_reason or "Payment declined",
                "transaction_id": payment.payment_reference if payment else None,
                "subscription_status": subscription.status.value if subscription else None
            },
            performed_by="payment_gateway_webhook",
            customer_id=invoice.customer_id,
            subscription_id=invoice.subscription_id
        )

        return {
            "status": "processed",
            "event": "payment_failed",
            "invoice_number": invoice.invoice_number,
            "invoice_status": invoice.status.value,
            "subscription_status": subscription.status.value if subscription else None,
            "transaction_id": payment.payment_reference if payment else None,
            "message": "Payment failed. Subscription moved to past_due."
        }

    elif clean_event == "payment_refunded":
        # 1. Invoice marked void
        invoice.status = InvoiceStatus.VOID
        invoice.updated_at = now

        # 2. Payment marked refunded
        if payment:
            payment.status = PaymentStatus.REFUNDED
            payment.updated_at = now

        db.commit()

        # 3. Audit Log
        create_audit_log(
            db=db,
            entity_type="payment",
            entity_id=payment.id if payment else invoice.id,
            action="payment_refunded",
            old_value={"invoice_status": "paid"},
            new_value={
                "invoice_number": invoice.invoice_number,
                "transaction_id": payment.payment_reference if payment else None,
                "status": "refunded"
            },
            performed_by="payment_gateway_webhook",
            customer_id=invoice.customer_id,
            subscription_id=invoice.subscription_id
        )

        return {
            "status": "processed",
            "event": "payment_refunded",
            "invoice_number": invoice.invoice_number,
            "invoice_status": invoice.status.value,
            "transaction_id": payment.payment_reference if payment else None,
            "message": "Payment refunded. Invoice marked as void."
        }

    else:
        raise ValueError(f"Unsupported webhook event '{event}'. Allowed: payment_success, payment_failed, payment_refunded.")


def process_mock_payment(
    db: Session,
    invoice_id: str,
    amount: Optional[Decimal] = None,
    payment_method: str = "credit_card",
    force_status: Optional[str] = None,
    success_rate: float = 0.80
) -> Dict[str, Any]:
    """
    Simulates payment gateway transaction for an invoice:
    - 80% Success, 20% Failure probability by default
    - Creates a Payment record with unique transaction ID
    - Triggers the payment webhook immediately
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice '{invoice_id}' not found.")

    if invoice.status == InvoiceStatus.PAID:
        raise ValueError(f"Invoice '{invoice.invoice_number}' is already paid.")

    pay_amount = amount if amount is not None else invoice.total_amount
    pay_amount = round(Decimal(str(pay_amount)), 2)

    now = datetime.now(timezone.utc)
    payment_ref = generate_unique_payment_reference(db)

    # Determine success vs failure (80% success by default, or force_status override)
    if force_status:
        is_success = force_status.strip().lower() in ["success", "paid"]
    else:
        is_success = random.random() < success_rate

    initial_status = PaymentStatus.SUCCESS if is_success else PaymentStatus.FAILED
    failure_reason = None if is_success else "Declined by issuing bank: Insufficient funds (Mock)"

    # Create Payment record
    payment = Payment(
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        payment_reference=payment_ref,
        amount=pay_amount,
        payment_method=payment_method,
        status=initial_status,
        payment_date=now if is_success else None,
        failure_reason=failure_reason,
        currency=invoice.currency or "USD"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Trigger webhook automatically
    event_name = "payment_success" if is_success else "payment_failed"
    webhook_result = handle_payment_webhook(
        db=db,
        event=event_name,
        invoice_id=invoice.id,
        payment_reference=payment_ref,
        amount=pay_amount,
        failure_reason=failure_reason
    )

    return {
        "payment_id": payment.id,
        "payment_reference": payment.payment_reference,
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "amount": float(payment.amount),
        "status": payment.status.value,
        "payment_date": payment.payment_date,
        "failure_reason": payment.failure_reason,
        "webhook_outcome": webhook_result
    }
