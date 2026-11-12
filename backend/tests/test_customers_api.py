import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, AuditLog
from app.schemas.schemas import CustomerCreate, CustomerUpdate
from app.api.endpoints.customers import create_customer, list_customers, get_customer, update_customer

class TestCustomerManagementAPIs(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_create_and_list_customers(self):
        cust_in = CustomerCreate(
            name="Alpha Corp",
            email="contact@alphacorp.io",
            company_name="Alpha Corporation Ltd",
            country="US"
        )
        created = create_customer(customer_in=cust_in, db=self.db)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, "Alpha Corp")
        self.assertEqual(created.company_name, "Alpha Corporation Ltd")

        # List customers
        all_customers = list_customers(db=self.db)
        self.assertEqual(len(all_customers), 1)

    def test_get_customer_by_id(self):
        cust = Customer(name="Beta Inc", email="info@beta.com", company_name="Beta Systems")
        self.db.add(cust)
        self.db.commit()

        fetched = get_customer(customer_id=cust.id, db=self.db)
        self.assertEqual(fetched.name, "Beta Inc")
        self.assertEqual(fetched.company_name, "Beta Systems")

    def test_update_customer(self):
        cust = Customer(name="Gamma LLC", email="gamma@llc.com", company_name="Old Gamma")
        self.db.add(cust)
        self.db.commit()

        update_in = CustomerUpdate(company_name="New Gamma Global", name="Gamma Holdings")
        updated = update_customer(customer_id=cust.id, customer_update=update_in, db=self.db)
        self.assertEqual(updated.company_name, "New Gamma Global")
        self.assertEqual(updated.name, "Gamma Holdings")

        # Verify audit log was recorded
        audit = self.db.query(AuditLog).filter(
            AuditLog.entity_type == "customer",
            AuditLog.entity_id == cust.id,
            AuditLog.action == "customer_updated"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.new_value["company_name"], "New Gamma Global")

if __name__ == "__main__":
    unittest.main()
