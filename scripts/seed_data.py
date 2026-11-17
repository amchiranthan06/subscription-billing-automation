"""Add sample plans and customers (safe to run more than once).  Run:  python -m scripts.seed_data"""
from sqlalchemy import select

from app.database import SessionLocal
from app.enums import BillingInterval
from app.models import Customer, Plan
from app.schemas import CustomerCreate, PlanCreate
from app.services import customer_service, plan_service

PLANS = [
    PlanCreate(
        name="Starter",
        description="For individuals and very small teams",
        price="499.00",
        billing_interval=BillingInterval.MONTHLY,
        trial_period_days=14,
        features={"max_users": 3, "storage_gb": 5, "support": "email"},
    ),
    PlanCreate(
        name="Pro",
        description="For growing teams",
        price="1499.00",
        billing_interval=BillingInterval.MONTHLY,
        trial_period_days=14,
        features={"max_users": 15, "storage_gb": 50, "support": "priority email"},
    ),
    PlanCreate(
        name="Enterprise Annual",
        description="Everything, billed once a year",
        price="49990.00",
        billing_interval=BillingInterval.ANNUAL,
        trial_period_days=30,
        features={"max_users": 500, "storage_gb": 1000, "support": "24x7 phone"},
    ),
]

CUSTOMERS = [
    CustomerCreate(name="Acme Corp", email="acme.billing@example.com", country="IN"),
    CustomerCreate(name="StartupXYZ", email="startupxyz.accounts@example.com", country="IN"),
]


def main() -> None:
    with SessionLocal() as db:
        for plan in PLANS:
            if db.scalar(select(Plan.id).where(Plan.name == plan.name)) is None:
                created = plan_service.create_plan(db, plan)
                print(f"Created plan {created.id}: {created.name}")
            else:
                print(f"Plan already exists: {plan.name}")
        for customer in CUSTOMERS:
            if db.scalar(select(Customer.id).where(Customer.email == customer.email.lower())) is None:
                created = customer_service.create_customer(db, customer)
                print(f"Created customer {created.id}: {created.name}")
            else:
                print(f"Customer already exists: {customer.email}")


if __name__ == "__main__":
    main()
