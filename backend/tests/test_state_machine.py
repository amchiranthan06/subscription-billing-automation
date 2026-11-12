import os
import sys
from datetime import datetime, timezone
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, AuditLog
from app.models.enums import SubscriptionStatus, BillingInterval
from app.services.state_machine import (
    transition_subscription, InvalidStateTransitionError, VALID_TRANSITIONS
)

class TestSubscriptionStatusStateMachine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed test customer and plan
        self.customer = Customer(name="Acme Corp", email="test@acmecorp.com")
        self.plan = Plan(name="Starter", code="starter", price=19.00, billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([self.customer, self.plan])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def _create_sub(self, initial_status: SubscriptionStatus) -> Subscription:
        now = datetime.now(timezone.utc)
        sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.plan.id,
            status=initial_status,
            start_date=now,
            end_date=now
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return sub

    # ----------------- 6 VALID TRANSITIONS (TASK 4) -----------------
    def test_transition_trial_to_active(self):
        sub = self._create_sub(SubscriptionStatus.TRIAL)
        transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE, reason="Trial period ended with payment")
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertIsNotNone(sub.updated_at)

    def test_transition_trial_to_cancelled(self):
        sub = self._create_sub(SubscriptionStatus.TRIAL)
        transition_subscription(self.db, sub, SubscriptionStatus.CANCELLED, reason="Cancelled during trial")
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)

    def test_transition_active_to_past_due(self):
        sub = self._create_sub(SubscriptionStatus.ACTIVE)
        transition_subscription(self.db, sub, SubscriptionStatus.PAST_DUE, reason="Card renewal charge failed")
        self.assertEqual(sub.status, SubscriptionStatus.PAST_DUE)

    def test_transition_active_to_cancelled(self):
        sub = self._create_sub(SubscriptionStatus.ACTIVE)
        transition_subscription(self.db, sub, SubscriptionStatus.CANCELLED, reason="User cancelled active subscription")
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)

    def test_transition_past_due_to_active(self):
        sub = self._create_sub(SubscriptionStatus.PAST_DUE)
        transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE, reason="Retry payment succeeded")
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

    def test_transition_past_due_to_cancelled(self):
        sub = self._create_sub(SubscriptionStatus.PAST_DUE)
        transition_subscription(self.db, sub, SubscriptionStatus.CANCELLED, reason="All 3 payment retries exhausted")
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)

    # ----------------- INVALID TRANSITIONS (TASK 4) -----------------
    def test_invalid_transition_cancelled_to_active(self):
        sub = self._create_sub(SubscriptionStatus.CANCELLED)
        with self.assertRaises(InvalidStateTransitionError) as ctx:
            transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE)
        self.assertIn("Cannot transition from 'cancelled' to 'active'", str(ctx.exception))

    def test_invalid_transition_trial_to_past_due(self):
        sub = self._create_sub(SubscriptionStatus.TRIAL)
        with self.assertRaises(InvalidStateTransitionError) as ctx:
            transition_subscription(self.db, sub, SubscriptionStatus.PAST_DUE)
        self.assertIn("Cannot transition from 'trial' to 'past_due'", str(ctx.exception))

    # ----------------- TIMESTAMPS & AUDIT LOGGING (TASK 4) -----------------
    def test_audit_logs_and_timestamps_recorded(self):
        sub = self._create_sub(SubscriptionStatus.TRIAL)
        transition_subscription(self.db, sub, SubscriptionStatus.ACTIVE, reason="First payment")
        transition_subscription(self.db, sub, SubscriptionStatus.PAST_DUE, reason="Renewal failed")
        transition_subscription(self.db, sub, SubscriptionStatus.CANCELLED, reason="Retries exhausted")

        logs = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == sub.id
        ).all()

        self.assertEqual(len(logs), 3)
        self.assertIsNotNone(sub.cancelled_at)
        self.assertIsNotNone(sub.updated_at)

if __name__ == "__main__":
    unittest.main()
