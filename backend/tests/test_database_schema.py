import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, inspect
from app.core.database import Base
from app.models.models import (
    Customer, Plan, Subscription, BillingCycle,
    Invoice, InvoiceLineItem, Payment, AuditLog
)

class TestDatabaseSchemaDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.engine)
        cls.inspector = inspect(cls.engine)

    def test_all_seven_tables_exist(self):
        tables = set(self.inspector.get_table_names())
        required_tables = {
            "plans",
            "customers",
            "subscriptions",
            "billing_cycles",
            "invoices",
            "payments",
            "audit_logs"
        }
        for table in required_tables:
            self.assertIn(table, tables, f"Table '{table}' is missing from schema")

    def test_plan_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("plans")}
        required_fields = {
            "name",
            "price",
            "billing_interval",
            "trial_days",
            "features",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'plans' table")

    def test_customer_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("customers")}
        required_fields = {
            "name",
            "email",
            "company_name",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'customers' table")

if __name__ == "__main__":
    unittest.main()
