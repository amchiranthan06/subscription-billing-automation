import os
import sys
from datetime import datetime, timezone
import unittest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, AuditLog
from app.models.enums import SubscriptionStatus, BillingInterval
from app.services.state_machine import transition_subscription, InvalidStateTransitionError

class TestSubscriptionStateMachine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_subscription_state_machine_happy_path(self):
        customer = Customer(name="Test Customer", email="test@example.com")
        plan = Plan(name="Starter", code="starter", price=19.00, billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([customer, plan])
        self.db.commit()

        now = datetime.now(timezone.utc)
        sub = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=now
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)

        # 1. Trial -> Active
        transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE, reason="Trial expired, charged successfully")
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

        # 2. Active -> Past Due (Payment failed)
        transition_subscription(self.db, sub, SubscriptionStatus.PAST_DUE, reason="Card payment failed on renewal")
        self.assertEqual(sub.status, SubscriptionStatus.PAST_DUE)

        # 3. Past Due -> Cancelled (Retries exhausted)
        transition_subscription(self.db, sub, SubscriptionStatus.CANCELLED, reason="3 retries failed")
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)

        # Check audit log records were written
        logs = self.db.query(AuditLog).filter(AuditLog.subscription_id == sub.id).all()
        self.assertEqual(len(logs), 3)

    def test_invalid_state_transition(self):
        customer = Customer(name="Test Customer 2", email="test2@example.com")
        plan = Plan(name="Pro", code="pro", price=49.00, billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([customer, plan])
        self.db.commit()

        now = datetime.now(timezone.utc)
        sub = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status=SubscriptionStatus.CANCELLED,
            current_period_start=now,
            current_period_end=now,
            cancelled_at=now
        )
        self.db.add(sub)
        self.db.commit()

        # Cancelled is a terminal state; cannot transition to ACTIVE
        with self.assertRaises(InvalidStateTransitionError):
            transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE, reason="Illegal resurrection")

if __name__ == "__main__":
    unittest.main()
