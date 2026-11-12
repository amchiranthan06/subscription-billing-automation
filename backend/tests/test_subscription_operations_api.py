import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, CancellationTiming
from app.schemas.schemas import SubscriptionChangePlan, SubscriptionCancel
from app.api.endpoints.subscriptions import (
    change_subscription_plan,
    pause_subscription,
    resume_subscription,
    cancel_subscription
)

class TestSubscriptionOperationsAPI(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="Alice Smith",
            email="alice@example.com",
            company_name="Acme Corp"
        )
        # Seed Plans
        self.basic_plan = Plan(
            name="Basic Monthly",
            code="basic_m",
            price=Decimal("19.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.pro_plan = Plan(
            name="Pro Monthly",
            code="pro_m",
            price=Decimal("49.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.archived_plan = Plan(
            name="Legacy Plan",
            code="legacy",
            price=Decimal("10.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=False
        )
        self.db.add_all([self.customer, self.basic_plan, self.pro_plan, self.archived_plan])
        self.db.commit()

        # Seed Active Subscription on Basic Plan
        now = datetime.now(timezone.utc)
        self.subscription = Subscription(
            customer_id=self.customer.id,
            plan_id=self.basic_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now + timedelta(days=30),
            cancel_at_period_end=False
        )
        self.db.add(self.subscription)
        self.db.commit()
        self.db.refresh(self.subscription)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_change_plan_success(self):
        """Test: Upgrades subscription from Basic to Pro plan and records audit log."""
        change_in = SubscriptionChangePlan(new_plan_id=self.pro_plan.id, prorate=True)
        updated = change_subscription_plan(
            subscription_id=self.subscription.id,
            plan_in=change_in,
            db=self.db
        )

        self.assertEqual(updated.plan_id, self.pro_plan.id)
        
        # Verify audit log
        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == self.subscription.id,
            AuditLog.action == "subscription_plan_changed"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.old_value["plan_id"], self.basic_plan.id)
        self.assertEqual(audit.new_value["plan_id"], self.pro_plan.id)

    def test_change_plan_invalid_scenarios(self):
        """Test: Changing to inactive plan, non-existent plan, or same plan raises 400/404."""
        # Non-existent plan
        with self.assertRaises(HTTPException) as ctx:
            change_subscription_plan(
                subscription_id=self.subscription.id,
                plan_in=SubscriptionChangePlan(new_plan_id="non_existent_id"),
                db=self.db
            )
        self.assertEqual(ctx.exception.status_code, 404)

        # Inactive plan
        with self.assertRaises(HTTPException) as ctx:
            change_subscription_plan(
                subscription_id=self.subscription.id,
                plan_in=SubscriptionChangePlan(new_plan_id=self.archived_plan.id),
                db=self.db
            )
        self.assertEqual(ctx.exception.status_code, 400)

        # Same plan
        with self.assertRaises(HTTPException) as ctx:
            change_subscription_plan(
                subscription_id=self.subscription.id,
                plan_in=SubscriptionChangePlan(new_plan_id=self.basic_plan.id),
                db=self.db
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_pause_and_resume_subscription(self):
        """Test: Pausing sets status=paused & paused_at; resuming restores status=active."""
        # Pause
        paused_sub = pause_subscription(subscription_id=self.subscription.id, db=self.db)
        self.assertEqual(paused_sub.status, SubscriptionStatus.PAUSED)
        self.assertIsNotNone(paused_sub.paused_at)

        # Resume
        resumed_sub = resume_subscription(subscription_id=self.subscription.id, db=self.db)
        self.assertEqual(resumed_sub.status, SubscriptionStatus.ACTIVE)
        self.assertIsNone(resumed_sub.paused_at)

    def test_cancel_immediate(self):
        """Test: Immediate cancellation sets status=cancelled and records cancelled_at."""
        cancel_in = SubscriptionCancel(
            timing=CancellationTiming.IMMEDIATE,
            reason="Customer decided to switch services"
        )
        cancelled_sub = cancel_subscription(
            subscription_id=self.subscription.id,
            cancel_in=cancel_in,
            db=self.db
        )
        self.assertEqual(cancelled_sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(cancelled_sub.cancelled_at)

    def test_cancel_end_of_cycle(self):
        """Test: End-of-cycle cancellation leaves status=active and sets cancel_at_period_end=True."""
        cancel_in = SubscriptionCancel(
            timing=CancellationTiming.END_OF_CYCLE,
            reason="End of billing cycle"
        )
        sub = cancel_subscription(
            subscription_id=self.subscription.id,
            cancel_in=cancel_in,
            db=self.db
        )
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertTrue(sub.cancel_at_period_end)

if __name__ == "__main__":
    unittest.main()
