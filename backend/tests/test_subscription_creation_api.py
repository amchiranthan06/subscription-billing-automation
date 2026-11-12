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
from app.models.models import Customer, Plan, Subscription, BillingCycle, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, BillingCycleStatus
from app.schemas.schemas import SubscriptionCreate
from app.api.endpoints.subscriptions import create_subscription

class TestSubscriptionCreationAPI(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="John Doe",
            email="john@example.com",
            company_name="Doe Enterprises"
        )
        # Seed Active Plan with 14-day trial
        self.plan = Plan(
            name="Pro Plan",
            code="pro",
            price=Decimal("49.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=14,
            is_active=True
        )
        self.db.add_all([self.customer, self.plan])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_create_subscription_with_trial(self):
        """Test: Validates customer/plan, assigns 14-day trial, status = trial."""
        sub_in = SubscriptionCreate(
            customer_id=self.customer.id,
            plan_id=self.plan.id,
            start_with_trial=True
        )
        sub = create_subscription(sub_in=sub_in, db=self.db)

        self.assertIsNotNone(sub.id)
        self.assertEqual(sub.customer_id, self.customer.id)
        self.assertEqual(sub.plan_id, self.plan.id)
        self.assertEqual(sub.status, SubscriptionStatus.TRIAL)
        self.assertIsNotNone(sub.trial_start)
        self.assertIsNotNone(sub.trial_end)
        self.assertIsNotNone(sub.start_date)
        self.assertIsNotNone(sub.end_date)
        
        # Verify 14-day calculation
        diff_days = (sub.end_date - sub.start_date).days
        self.assertEqual(diff_days, 14)

        # Verify BillingCycle record created
        cycle = self.db.query(BillingCycle).filter(BillingCycle.subscription_id == sub.id).first()
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle.status, BillingCycleStatus.PENDING)

        # Verify AuditLog recorded
        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == sub.id,
            AuditLog.action == "subscription_created"
        ).first()
        self.assertIsNotNone(audit)

    def test_create_subscription_immediate_active(self):
        """Test: Subscribe without trial -> status = active, end_date = 1 month later."""
        sub_in = SubscriptionCreate(
            customer_id=self.customer.id,
            plan_id=self.plan.id,
            start_with_trial=False
        )
        sub = create_subscription(sub_in=sub_in, db=self.db)

        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertIsNone(sub.trial_start)
        self.assertIsNone(sub.trial_end)
        self.assertIsNotNone(sub.start_date)
        self.assertIsNotNone(sub.end_date)
        
        # Approximately 30-31 days for 1 month
        diff_days = (sub.end_date - sub.start_date).days
        self.assertIn(diff_days, [28, 29, 30, 31])

    def test_validation_non_existent_customer(self):
        """Test: Raises 404 when customer does not exist."""
        sub_in = SubscriptionCreate(
            customer_id="non_existent_uuid",
            plan_id=self.plan.id
        )
        with self.assertRaises(HTTPException) as ctx:
            create_subscription(sub_in=sub_in, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("Customer not found", ctx.exception.detail)

    def test_validation_non_existent_or_inactive_plan(self):
        """Test: Raises 400 when plan does not exist or is inactive."""
        # Inactive plan
        inactive_plan = Plan(name="Old Tier", code="old", price=Decimal("10.00"), is_active=False)
        self.db.add(inactive_plan)
        self.db.commit()

        sub_in = SubscriptionCreate(
            customer_id=self.customer.id,
            plan_id=inactive_plan.id
        )
        with self.assertRaises(HTTPException) as ctx:
            create_subscription(sub_in=sub_in, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Active plan required", ctx.exception.detail)

if __name__ == "__main__":
    unittest.main()
