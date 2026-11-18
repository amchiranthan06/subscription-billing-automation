import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, BillingCycle, Invoice, InvoiceLineItem, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, BillingCycleStatus, LineItemType
from app.schemas.schemas import SubscriptionChangePlan, ProrationPreviewRequest
from app.services.proration import calculate_proration, preview_plan_change, apply_plan_change_with_proration
from app.api.endpoints.subscriptions import get_proration_preview, change_subscription_plan, get_subscription_plan_history


class TestProrationLogic(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="Sarah Connor",
            email="sarah@example.com",
            company_name="Cyberdyne Resistance"
        )
        # Seed Pro Plan ($1000.00 / month)
        self.pro_plan = Plan(
            name="Pro Plan",
            code="pro-plan",
            price=Decimal("1000.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        # Seed Premium Plan ($2000.00 / month)
        self.premium_plan = Plan(
            name="Premium Plan",
            code="premium-plan",
            price=Decimal("2000.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.db.add_all([self.customer, self.pro_plan, self.premium_plan])
        self.db.commit()

        # Seed Subscription starting 15 days ago, ending 15 days from now
        now = datetime.now(timezone.utc)
        self.start_date = now - timedelta(days=15)
        self.end_date = now + timedelta(days=15)

        self.sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.db.add(self.sub)
        self.db.commit()

        # Seed Billing Cycle
        self.cycle = BillingCycle(
            subscription_id=self.sub.id,
            cycle_start_date=self.start_date,
            cycle_end_date=self.end_date,
            renewal_date=self.end_date,
            status=BillingCycleStatus.PENDING,
            cycle_index=1
        )
        self.db.add(self.cycle)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_calculate_proration_mid_cycle_upgrade(self):
        """Test: Mid-cycle upgrade math (15 days used, 15 days remaining in 30-day cycle)."""
        res = calculate_proration(
            start_date=self.start_date,
            end_date=self.end_date,
            current_price=Decimal("1000.00"),
            new_price=Decimal("2000.00"),
            change_date=self.start_date + timedelta(days=15)
        )

        self.assertEqual(res["total_days"], 30)
        self.assertEqual(res["remaining_days"], 15)
        self.assertAlmostEqual(res["remaining_ratio"], 0.5, places=2)
        self.assertEqual(res["unused_credit"], Decimal("500.00"))
        self.assertEqual(res["new_charge"], Decimal("1000.00"))
        self.assertEqual(res["net_amount_due"], Decimal("500.00"))
        self.assertTrue(res["is_upgrade"])
        self.assertFalse(res["is_downgrade"])

    def test_calculate_proration_mid_cycle_downgrade(self):
        """Test: Mid-cycle downgrade math (Premium $2000 -> Pro $1000 with 15 days remaining)."""
        res = calculate_proration(
            start_date=self.start_date,
            end_date=self.end_date,
            current_price=Decimal("2000.00"),
            new_price=Decimal("1000.00"),
            change_date=self.start_date + timedelta(days=15)
        )

        self.assertEqual(res["unused_credit"], Decimal("1000.00"))
        self.assertEqual(res["new_charge"], Decimal("500.00"))
        self.assertEqual(res["net_amount_due"], Decimal("-500.00"))
        self.assertTrue(res["is_downgrade"])
        self.assertFalse(res["is_upgrade"])

    def test_preview_plan_change_endpoint(self):
        """Test: Proration preview endpoint returns exact financial forecast without modifying subscription."""
        payload = ProrationPreviewRequest(new_plan_id=self.premium_plan.id)
        preview = get_proration_preview(
            subscription_id=self.sub.id,
            payload=payload,
            db=self.db
        )

        self.assertEqual(preview["current_plan"]["name"], "Pro Plan")
        self.assertEqual(preview["new_plan"]["name"], "Premium Plan")
        self.assertEqual(preview["proration"]["unused_credit"], Decimal("500.00"))
        self.assertEqual(preview["proration"]["new_charge"], Decimal("1000.00"))
        self.assertEqual(preview["proration"]["net_amount_due"], Decimal("500.00"))

        # Verify subscription was NOT changed in DB during preview
        refreshed_sub = self.db.query(Subscription).filter(Subscription.id == self.sub.id).first()
        self.assertEqual(refreshed_sub.plan_id, self.pro_plan.id)

    def test_apply_plan_change_creates_adjustment_invoice_and_audit(self):
        """Test: Confirming plan change updates subscription, creates adjustment invoice with line items & audit log."""
        plan_in = SubscriptionChangePlan(new_plan_id=self.premium_plan.id, prorate=True)
        updated_sub = change_subscription_plan(
            subscription_id=self.sub.id,
            plan_in=plan_in,
            db=self.db
        )

        # 1. Verify subscription updated to new plan
        self.assertEqual(updated_sub.plan_id, self.premium_plan.id)

        # 2. Verify adjustment invoice was generated
        invoice = self.db.query(Invoice).filter(Invoice.subscription_id == self.sub.id).first()
        self.assertIsNotNone(invoice)
        self.assertTrue(invoice.invoice_number.startswith("INV-"))
        self.assertEqual(invoice.subtotal, Decimal("500.00")) # net amount due
        self.assertEqual(invoice.total_amount, Decimal("550.00")) # subtotal + 10% tax

        # 3. Verify line items (credit and debit)
        line_items = self.db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice.id).all()
        self.assertEqual(len(line_items), 2)
        types = [item.line_item_type for item in line_items]
        self.assertIn(LineItemType.PRORATION_CREDIT, types)
        self.assertIn(LineItemType.PRORATION_DEBIT, types)

        # 4. Verify audit log entry
        audit = self.db.query(AuditLog).filter(
            AuditLog.subscription_id == self.sub.id,
            AuditLog.action == "plan_changed"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.old_value["plan_name"], "Pro Plan")
        self.assertEqual(audit.new_value["plan_name"], "Premium Plan")
        self.assertEqual(audit.new_value["net_amount_due"], 500.0)

    def test_plan_change_history_timeline(self):
        """Test: Plan history endpoint returns chronological timeline of plan changes."""
        # Execute upgrade Pro -> Premium
        plan_in = SubscriptionChangePlan(new_plan_id=self.premium_plan.id, prorate=True)
        change_subscription_plan(self.sub.id, plan_in, self.db)

        history = get_subscription_plan_history(self.sub.id, self.db)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["from_plan"], "Pro Plan")
        self.assertEqual(history[0]["to_plan"], "Premium Plan")
        self.assertEqual(history[0]["net_adjustment"], Decimal("500.00"))
