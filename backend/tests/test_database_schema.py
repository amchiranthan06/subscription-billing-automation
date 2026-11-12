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
            "users",
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

    def test_users_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("users")}
        required_fields = {
            "name",
            "email",
            "hashed_password",
            "role",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'users' table")

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

    def test_subscription_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("subscriptions")}
        required_fields = {
            "customer_id",
            "plan_id",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'subscriptions' table")

    def test_billing_cycles_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("billing_cycles")}
        required_fields = {
            "subscription_id",
            "cycle_start_date",
            "cycle_end_date",
            "renewal_date",
            "status",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'billing_cycles' table")

    def test_invoice_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("invoices")}
        required_fields = {
            "invoice_number",
            "subscription_id",
            "customer_id",
            "invoice_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "total_amount",
            "status"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'invoices' table")

    def test_payment_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("payments")}
        required_fields = {
            "invoice_id",
            "payment_reference",
            "amount",
            "payment_method",
            "status",
            "payment_date",
            "created_at",
            "updated_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'payments' table")

    def test_audit_logs_table_fields(self):
        columns = {col["name"] for col in self.inspector.get_columns("audit_logs")}
        required_fields = {
            "entity_type",
            "entity_id",
            "action",
            "old_value",
            "new_value",
            "performed_by",
            "created_at"
        }
        for field in required_fields:
            self.assertIn(field, columns, f"Column '{field}' is missing from 'audit_logs' table")

if __name__ == "__main__":
    unittest.main()
