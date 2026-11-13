import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, CancellationTiming
from app.schemas.schemas import (
    PlanCreate, PlanUpdate, CustomerCreate, SubscriptionCreate,
    SubscriptionChangePlan, SubscriptionCancel
)
from app.api.endpoints.plans import create_plan, update_plan
from app.api.endpoints.customers import create_customer
from app.api.endpoints.subscriptions import (
    create_subscription, change_subscription_plan, cancel_subscription
)

class TestAuditLoggingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_log_event_plan_created(self):
        """Task 10: Automatically logs event 'plan_created' when a plan is created."""
        plan_in = PlanCreate(
            name="Audit Test Plan",
            code="audit_test",
            price=Decimal("29.99"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=7
        )
        plan = create_plan(plan_in=plan_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "plan",
            AuditLog.entity_id == plan.id,
            AuditLog.action == "plan_created"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "plan_created")
        self.assertEqual(audit.new_value["name"], "Audit Test Plan")
        self.assertIsNotNone(audit.created_at)

    def test_log_event_plan_updated(self):
        """Task 10: Automatically logs event 'plan_updated' when a plan is modified."""
        plan = Plan(
            name="Old Name",
            code="old_code",
            price=Decimal("10.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.db.add(plan)
        self.db.commit()

        update_in = PlanUpdate(name="New Brand Name", price=Decimal("19.99"))
        updated_plan = update_plan(plan_id=plan.id, plan_update=update_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "plan",
            AuditLog.entity_id == plan.id,
            AuditLog.action == "plan_updated"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.old_value["name"], "Old Name")
        self.assertEqual(audit.new_value["name"], "New Brand Name")

    def test_log_event_customer_created(self):
        """Task 10: Automatically logs event 'customer_created' when a customer is registered."""
        cust_in = CustomerCreate(
            name="Grace Hopper",
            email="grace@navy.mil",
            company_name="US Navy"
        )
        customer = create_customer(customer_in=cust_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "customer",
            AuditLog.entity_id == customer.id,
            AuditLog.action == "customer_created"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.new_value["email"], "grace@navy.mil")
        self.assertEqual(audit.customer_id, customer.id)

    def test_log_event_subscription_created(self):
        """Task 10: Automatically logs event 'subscription_created' when a subscription is started."""
        cust = Customer(name="Alan Turing", email="alan@bletchley.uk")
        plan = Plan(name="Enigma Plan", code="enigma", price=Decimal("50.00"), billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([cust, plan])
        self.db.commit()

        sub_in = SubscriptionCreate(customer_id=cust.id, plan_id=plan.id, start_with_trial=False)
        sub = create_subscription(sub_in=sub_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == sub.id,
            AuditLog.action == "subscription_created"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.subscription_id, sub.id)
        self.assertEqual(audit.customer_id, cust.id)

    def test_log_event_plan_changed(self):
        """Task 10: Automatically logs event 'plan_changed' when switching subscription plans."""
        cust = Customer(name="Ada Lovelace", email="ada@analytical.org")
        plan_a = Plan(name="Plan Tier A", code="tier_a", price=Decimal("20.00"), billing_interval=BillingInterval.MONTHLY)
        plan_b = Plan(name="Plan Tier B", code="tier_b", price=Decimal("40.00"), billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([cust, plan_a, plan_b])
        self.db.commit()

        sub = Subscription(
            customer_id=cust.id,
            plan_id=plan_a.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        self.db.add(sub)
        self.db.commit()

        change_in = SubscriptionChangePlan(new_plan_id=plan_b.id, prorate=True)
        change_subscription_plan(subscription_id=sub.id, plan_in=change_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == sub.id,
            AuditLog.action == "plan_changed"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.old_value["plan_id"], plan_a.id)
        self.assertEqual(audit.new_value["plan_id"], plan_b.id)

    def test_log_event_subscription_cancelled(self):
        """Task 10: Automatically logs event 'subscription_cancelled' upon immediate or scheduled cancellation."""
        cust = Customer(name="Linus Torvalds", email="linus@linux.org")
        plan = Plan(name="Kernel Plan", code="kernel", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY)
        self.db.add_all([cust, plan])
        self.db.commit()

        sub = Subscription(
            customer_id=cust.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        self.db.add(sub)
        self.db.commit()

        # Immediate cancellation
        cancel_in = SubscriptionCancel(timing=CancellationTiming.IMMEDIATE, reason="Project done")
        cancel_subscription(subscription_id=sub.id, cancel_in=cancel_in, db=self.db)

        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "subscription",
            AuditLog.entity_id == sub.id,
            AuditLog.action == "subscription_cancelled"
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "subscription_cancelled")
        self.assertEqual(audit.new_value["status"], SubscriptionStatus.CANCELLED.value)

if __name__ == "__main__":
    unittest.main()
