import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, BillingCycle, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus, BillingCycleStatus
from app.services.billing_cycle import (
    calculate_next_renewal_date,
    generate_billing_cycle,
    get_billing_cycle_history
)

class TestBillingCycleEngine(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="Charlie Brown",
            email="charlie@example.com",
            company_name="Peanuts Inc"
        )
        # Seed Monthly Plan
        self.monthly_plan = Plan(
            name="Starter Monthly",
            code="starter_m",
            price=Decimal("15.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        # Seed Annual Plan
        self.annual_plan = Plan(
            name="Enterprise Annual",
            code="enterprise_a",
            price=Decimal("150.00"),
            billing_interval=BillingInterval.ANNUAL,
            trial_days=0,
            is_active=True
        )
        self.db.add_all([self.customer, self.monthly_plan, self.annual_plan])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_monthly_plan_creates_next_renewal_date(self):
        """Task 9: Monthly plans create renewal date +1 month from start date."""
        start_date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        renewal = calculate_next_renewal_date(start_date, BillingInterval.MONTHLY)
        expected = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(renewal, expected)

        # End of month boundary test (Jan 31 -> Feb 28)
        jan_31 = datetime(2026, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
        feb_end = calculate_next_renewal_date(jan_31, BillingInterval.MONTHLY)
        self.assertEqual(feb_end.month, 2)
        self.assertEqual(feb_end.day, 28)

    def test_annual_plan_creates_next_renewal_date(self):
        """Task 9: Annual plans create renewal date +1 year from start date."""
        start_date = datetime(2026, 5, 20, 14, 30, 0, tzinfo=timezone.utc)
        renewal = calculate_next_renewal_date(start_date, BillingInterval.ANNUAL)
        expected = datetime(2027, 5, 20, 14, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(renewal, expected)

    def test_generate_billing_cycle_and_store_history(self):
        """Task 9: Generates sequential billing cycles and stores complete cycle history."""
        start_date = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.monthly_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            end_date=start_date + relativedelta(months=1)
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)

        # 1. Generate Cycle 1
        cycle_1 = generate_billing_cycle(db=self.db, subscription_id=sub.id)
        self.assertEqual(cycle_1.cycle_index, 1)
        self.assertEqual(cycle_1.status, BillingCycleStatus.PENDING)
        self.assertEqual(cycle_1.cycle_start_date.replace(tzinfo=timezone.utc), start_date)
        self.assertEqual(cycle_1.cycle_end_date.replace(tzinfo=timezone.utc), start_date + relativedelta(months=1))
        self.assertEqual(cycle_1.renewal_date, cycle_1.cycle_end_date)

        # 2. Generate Cycle 2 (Rolls over: Cycle 1 marked COMPLETED, Cycle 2 created PENDING)
        cycle_2 = generate_billing_cycle(db=self.db, subscription_id=sub.id)
        self.assertEqual(cycle_2.cycle_index, 2)
        self.assertEqual(cycle_2.status, BillingCycleStatus.PENDING)
        self.assertEqual(cycle_2.cycle_start_date, cycle_1.cycle_end_date)
        self.assertEqual(cycle_2.cycle_end_date, cycle_1.cycle_end_date + relativedelta(months=1))

        # Check Cycle 1 is now COMPLETED
        self.db.refresh(cycle_1)
        self.assertEqual(cycle_1.status, BillingCycleStatus.COMPLETED)

        # 3. Verify history stores both records
        history = get_billing_cycle_history(db=self.db, subscription_id=sub.id)
        self.assertEqual(len(history), 2)
        self.assertEqual([c.cycle_index for c in history], [1, 2])
        self.assertEqual(history[0].status, BillingCycleStatus.COMPLETED)
        self.assertEqual(history[1].status, BillingCycleStatus.PENDING)

    def test_annual_subscription_cycle_generation(self):
        """Task 9: Generates 1-year cycle for annual plans."""
        start_date = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.annual_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            end_date=start_date + relativedelta(years=1)
        )
        self.db.add(sub)
        self.db.commit()

        cycle = generate_billing_cycle(db=self.db, subscription_id=sub.id)
        self.assertEqual(cycle.cycle_index, 1)
        self.assertEqual(cycle.cycle_end_date.replace(tzinfo=timezone.utc), start_date + relativedelta(years=1))
        self.assertEqual(cycle.renewal_date.replace(tzinfo=timezone.utc), start_date + relativedelta(years=1))

if __name__ == "__main__":
    unittest.main()
