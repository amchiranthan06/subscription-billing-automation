import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, BillingCycle, Invoice, Payment, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, BillingCycleStatus, InvoiceStatus, PaymentStatus
from app.schemas.schemas import PaymentProcessRequest, PaymentWebhookPayload
from app.services.payment import (
    generate_unique_payment_reference,
    process_mock_payment,
    handle_payment_webhook
)
from app.api.endpoints.payments import process_payment_endpoint, list_payments
from app.api.endpoints.webhooks import receive_payment_webhook


class TestMockPaymentGateway(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="John Connor",
            email="john@resistance.org",
            company_name="Tech Solutions"
        )
        # Seed Plan ($499.00 / month)
        self.plan = Plan(
            name="Business Tier",
            code="business-tier",
            price=Decimal("499.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.db.add_all([self.customer, self.plan])
        self.db.commit()

        # Seed Active Subscription
        now = datetime.now(timezone.utc)
        self.sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now + timedelta(days=30)
        )
        self.db.add(self.sub)
        self.db.commit()

        # Seed Unpaid Invoice ($499.00 + $49.90 tax = $548.90)
        self.invoice = Invoice(
            invoice_number="INV-202611-9001",
            customer_id=self.customer.id,
            subscription_id=self.sub.id,
            invoice_date=now,
            due_date=now + timedelta(days=14),
            subtotal=Decimal("499.00"),
            tax_amount=Decimal("49.90"),
            total_amount=Decimal("548.90"),
            status=InvoiceStatus.UNPAID,
            currency="USD"
        )
        self.db.add(self.invoice)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_unique_payment_reference_generation(self):
        """Test: Generates unique transaction ID in format TXN-YYYYMMDD-XXXXX."""
        ref1 = generate_unique_payment_reference(self.db)
        p1 = Payment(
            invoice_id=self.invoice.id,
            payment_reference=ref1,
            amount=Decimal("499.00"),
            status=PaymentStatus.PENDING
        )
        self.db.add(p1)
        self.db.commit()

        ref2 = generate_unique_payment_reference(self.db)
        self.assertTrue(ref1.startswith("TXN-"))
        self.assertTrue(ref2.startswith("TXN-"))
        self.assertNotEqual(ref1, ref2)

    def test_process_payment_success_flow(self):
        """Test: Payment succeeds -> Invoice becomes PAID, Subscription remains ACTIVE, audit log written."""
        req = PaymentProcessRequest(
            invoice_id=self.invoice.id,
            amount=Decimal("548.90"),
            payment_method="credit_card",
            force_status="success"
        )

        resp = process_payment_endpoint(payload=req, db=self.db)

        # 1. Check response
        self.assertEqual(resp["status"], "success")
        self.assertTrue(resp["payment_reference"].startswith("TXN-"))

        # 2. Check Invoice updated to PAID
        refreshed_inv = self.db.query(Invoice).filter(Invoice.id == self.invoice.id).first()
        self.assertEqual(refreshed_inv.status, InvoiceStatus.PAID)
        self.assertIsNotNone(refreshed_inv.paid_at)

        # 3. Check Subscription remains ACTIVE
        refreshed_sub = self.db.query(Subscription).filter(Subscription.id == self.sub.id).first()
        self.assertEqual(refreshed_sub.status, SubscriptionStatus.ACTIVE)

        # 4. Check Payment record stored
        payment_record = self.db.query(Payment).filter(Payment.invoice_id == self.invoice.id).first()
        self.assertIsNotNone(payment_record)
        self.assertEqual(payment_record.status, PaymentStatus.SUCCESS)

        # 5. Check Audit log
        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_id == payment_record.id,
            AuditLog.action == "payment_success"
        ).first()
        self.assertIsNotNone(audit)

    def test_process_payment_failure_flow(self):
        """Test: Payment fails -> Invoice remains UNPAID, Subscription moves ACTIVE -> PAST_DUE."""
        req = PaymentProcessRequest(
            invoice_id=self.invoice.id,
            amount=Decimal("548.90"),
            payment_method="credit_card",
            force_status="failed"
        )

        resp = process_payment_endpoint(payload=req, db=self.db)

        # 1. Check response
        self.assertEqual(resp["status"], "failed")
        self.assertIsNotNone(resp["failure_reason"])

        # 2. Check Invoice remains UNPAID
        refreshed_inv = self.db.query(Invoice).filter(Invoice.id == self.invoice.id).first()
        self.assertEqual(refreshed_inv.status, InvoiceStatus.UNPAID)
        self.assertIsNone(refreshed_inv.paid_at)

        # 3. Check Subscription transitioned to PAST_DUE
        refreshed_sub = self.db.query(Subscription).filter(Subscription.id == self.sub.id).first()
        self.assertEqual(refreshed_sub.status, SubscriptionStatus.PAST_DUE)

        # 4. Check Payment record has failure reason and retry_count
        payment_record = self.db.query(Payment).filter(Payment.invoice_id == self.invoice.id).first()
        self.assertEqual(payment_record.status, PaymentStatus.FAILED)
        self.assertGreaterEqual(payment_record.retry_count, 1)

    def test_webhook_payment_success_direct(self):
        """Test: Direct POST /webhooks/payment with payment_success event updates state."""
        payload = PaymentWebhookPayload(
            event="payment_success",
            invoice_id=self.invoice.id,
            payment_reference="TXN-MANUAL-001",
            amount=Decimal("548.90")
        )

        result = receive_payment_webhook(payload=payload, db=self.db)
        self.assertEqual(result["event"], "payment_success")
        self.assertEqual(result["invoice_status"], "paid")

        refreshed_inv = self.db.query(Invoice).filter(Invoice.id == self.invoice.id).first()
        self.assertEqual(refreshed_inv.status, InvoiceStatus.PAID)

    def test_webhook_payment_failed_direct(self):
        """Test: Direct POST /webhooks/payment with payment_failed event updates subscription to past_due."""
        payload = PaymentWebhookPayload(
            event="payment_failed",
            invoice_id=self.invoice.id,
            payment_reference="TXN-MANUAL-002",
            failure_reason="Card expired"
        )

        result = receive_payment_webhook(payload=payload, db=self.db)
        self.assertEqual(result["event"], "payment_failed")
        self.assertEqual(result["subscription_status"], "past_due")

        refreshed_sub = self.db.query(Subscription).filter(Subscription.id == self.sub.id).first()
        self.assertEqual(refreshed_sub.status, SubscriptionStatus.PAST_DUE)

    def test_webhook_payment_refunded(self):
        """Test: Webhook payment_refunded marks invoice VOID and payment REFUNDED."""
        # First pay it
        process_mock_payment(self.db, self.invoice.id, force_status="success")

        # Now trigger refund webhook
        payload = PaymentWebhookPayload(
            event="payment_refunded",
            invoice_id=self.invoice.id
        )
        result = receive_payment_webhook(payload=payload, db=self.db)
        self.assertEqual(result["event"], "payment_refunded")
        self.assertEqual(result["invoice_status"], "void")

        refreshed_inv = self.db.query(Invoice).filter(Invoice.id == self.invoice.id).first()
        self.assertEqual(refreshed_inv.status, InvoiceStatus.VOID)

    def test_already_paid_invoice_guard(self):
        """Test: Attempting to process payment for an already paid invoice raises error."""
        process_mock_payment(self.db, self.invoice.id, force_status="success")
        with self.assertRaises(ValueError):
            process_mock_payment(self.db, self.invoice.id, force_status="success")
