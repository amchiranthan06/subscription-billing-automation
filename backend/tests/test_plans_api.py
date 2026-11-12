import os
import sys
import unittest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Plan, Customer, Subscription, AuditLog
from app.models.enums import BillingInterval, SubscriptionStatus
from app.schemas.schemas import PlanCreate, PlanUpdate
from app.api.endpoints.plans import create_plan, list_plans, get_plan, update_plan, archive_plan, delete_plan

class TestPlanManagementAPIs(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_create_and_list_plans(self):
        plan_in = PlanCreate(
            name="Scale Plan",
            price=Decimal("79.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=14,
            features={"analytics": True, "seats": 20}
        )
        created = create_plan(plan_in=plan_in, db=self.db)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, "Scale Plan")
        self.assertEqual(created.price, Decimal("79.00"))
        self.assertTrue(created.is_active)

        # List plans
        all_plans = list_plans(db=self.db)
        self.assertEqual(len(all_plans), 1)

    def test_update_plan(self):
        plan = Plan(name="Starter", code="starter", price=Decimal("19.00"), billing_interval=BillingInterval.MONTHLY)
        self.db.add(plan)
        self.db.commit()

        update_in = PlanUpdate(price=Decimal("25.00"), name="Starter Plus")
        updated = update_plan(plan_id=plan.id, plan_update=update_in, db=self.db)
        self.assertEqual(updated.price, Decimal("25.00"))
        self.assertEqual(updated.name, "Starter Plus")

    def test_archive_plan(self):
        plan = Plan(name="Pro Plan", code="pro", price=Decimal("49.00"), billing_interval=BillingInterval.MONTHLY, is_active=True)
        self.db.add(plan)
        self.db.commit()

        archived = archive_plan(plan_id=plan.id, db=self.db)
        self.assertFalse(archived.is_active)

    def test_delete_plan_success_and_guard(self):
        # 1. Unused plan can be deleted
        plan_free = Plan(name="Free Tier", code="free", price=Decimal("0.00"), billing_interval=BillingInterval.MONTHLY)
        self.db.add(plan_free)
        self.db.commit()

        res = delete_plan(plan_id=plan_free.id, db=self.db)
        self.assertIn("deleted successfully", res["message"])
        self.assertIsNone(self.db.query(Plan).filter(Plan.id == plan_free.id).first())

        # 2. Plan with active subscription cannot be deleted
        plan_used = Plan(name="Business", code="business", price=Decimal("99.00"), billing_interval=BillingInterval.MONTHLY)
        customer = Customer(name="Big Corp", email="corp@example.com")
        self.db.add_all([plan_used, customer])
        self.db.commit()

        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        sub = Subscription(
            customer_id=customer.id,
            plan_id=plan_used.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now
        )
        self.db.add(sub)
        self.db.commit()

        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            delete_plan(plan_id=plan_used.id, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Cannot delete plan", ctx.exception.detail)

if __name__ == "__main__":
    unittest.main()
