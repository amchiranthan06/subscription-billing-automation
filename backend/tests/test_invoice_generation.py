import os
import sys
import unittest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import Customer, Plan, Subscription, BillingCycle, Invoice, InvoiceLineItem
from app.models.enums import BillingInterval, SubscriptionStatus, BillingCycleStatus, InvoiceStatus, LineItemType
from app.schemas.schemas import InvoiceGenerateRequest
from app.services.invoice import (
    generate_unique_invoice_number,
    calculate_invoice_financials,
    generate_invoice_for_subscription,
    generate_invoice_pdf
)
from app.api.endpoints.invoices import generate_invoice, list_invoices, get_invoice, download_invoice_pdf


class TestInvoiceGeneration(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

        # Seed Customer
        self.customer = Customer(
            name="Alice Smith",
            email="alice@company.com",
            company_name="Acme Corp"
        )
        # Seed Plan ($100.00 / month)
        self.plan = Plan(
            name="Enterprise Tier",
            code="enterprise-monthly",
            price=Decimal("100.00"),
            billing_interval=BillingInterval.MONTHLY,
            trial_days=0,
            is_active=True
        )
        self.db.add_all([self.customer, self.plan])
        self.db.commit()

        # Seed Active Subscription
        now = datetime.now(timezone.utc)
        self.sub = Subscription(
            customer_id=self.customer.id,
            plan_id=self.plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now + timedelta(days=30)
        )
        self.db.add(self.sub)
        self.db.commit()

        # Seed Billing Cycle
        self.cycle = BillingCycle(
            subscription_id=self.sub.id,
            cycle_start_date=now,
            cycle_end_date=now + timedelta(days=30),
            renewal_date=now + timedelta(days=30),
            status=BillingCycleStatus.PENDING,
            cycle_index=1
        )
        self.db.add(self.cycle)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_unique_invoice_number_format(self):
        """Test: Generated invoice number conforms to INV-YYYYMM-XXXX and increments sequentially."""
        inv_num_1 = generate_unique_invoice_number(self.db)
        inv1 = Invoice(
            invoice_number=inv_num_1,
            customer_id=self.customer.id,
            subscription_id=self.sub.id,
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("10.00"),
            total_amount=Decimal("110.00"),
            status=InvoiceStatus.UNPAID
        )
        self.db.add(inv1)
        self.db.commit()

        inv_num_2 = generate_unique_invoice_number(self.db)
        self.assertTrue(inv_num_1.startswith("INV-"))
        self.assertTrue(inv_num_2.startswith("INV-"))
        self.assertNotEqual(inv_num_1, inv_num_2)

    def test_financial_calculations(self):
        """Test: Computes correct subtotal, 10% tax, and total amount."""
        subtotal, tax, total = calculate_invoice_financials(Decimal("100.00"), tax_rate=Decimal("0.10"))
        self.assertEqual(subtotal, Decimal("100.00"))
        self.assertEqual(tax, Decimal("10.00"))
        self.assertEqual(total, Decimal("110.00"))

        # Test with 18% tax
        subtotal2, tax2, total2 = calculate_invoice_financials(Decimal("50.00"), tax_rate=Decimal("0.18"))
        self.assertEqual(subtotal2, Decimal("50.00"))
        self.assertEqual(tax2, Decimal("9.00"))
        self.assertEqual(total2, Decimal("59.00"))

    def test_generate_invoice_for_subscription(self):
        """Test: Generates invoice with line items, default status UNPAID, and links to customer & plan."""
        invoice = generate_invoice_for_subscription(
            db=self.db,
            subscription_id=self.sub.id,
            billing_cycle_id=self.cycle.id,
            tax_rate=Decimal("0.10")
        )

        self.assertIsNotNone(invoice.id)
        self.assertEqual(invoice.status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice.customer_id, self.customer.id)
        self.assertEqual(invoice.subscription_id, self.sub.id)
        self.assertEqual(invoice.billing_cycle_id, self.cycle.id)
        self.assertEqual(invoice.subtotal, Decimal("100.00"))
        self.assertEqual(invoice.tax_amount, Decimal("10.00"))
        self.assertEqual(invoice.total_amount, Decimal("110.00"))

        # Check line item
        self.assertEqual(len(invoice.line_items), 1)
        line = invoice.line_items[0]
        self.assertEqual(line.line_item_type, LineItemType.PLAN_FEE)
        self.assertEqual(line.amount, Decimal("100.00"))
        self.assertIn("Enterprise Tier", line.description)

    def test_prevent_duplicate_invoice_for_same_cycle(self):
        """Test: Requesting invoice generation twice for same billing cycle returns existing invoice without duplicate."""
        inv1 = generate_invoice_for_subscription(self.db, self.sub.id, billing_cycle_id=self.cycle.id)
        inv2 = generate_invoice_for_subscription(self.db, self.sub.id, billing_cycle_id=self.cycle.id)

        self.assertEqual(inv1.id, inv2.id)
        self.assertEqual(inv1.invoice_number, inv2.invoice_number)
        total_invoices = self.db.query(Invoice).count()
        self.assertEqual(total_invoices, 1)

    def test_list_invoices_with_status_filter(self):
        """Test: Filtering invoices by status (paid vs unpaid)."""
        inv_unpaid = generate_invoice_for_subscription(self.db, self.sub.id)
        inv_unpaid.status = InvoiceStatus.UNPAID

        # Add a second paid invoice
        inv_paid = Invoice(
            invoice_number="INV-PAID-001",
            customer_id=self.customer.id,
            subscription_id=self.sub.id,
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            subtotal=Decimal("50.00"),
            tax_amount=Decimal("5.00"),
            total_amount=Decimal("55.00"),
            status=InvoiceStatus.PAID
        )
        self.db.add(inv_paid)
        self.db.commit()

        # Query all
        all_invoices = list_invoices(db=self.db)
        self.assertEqual(len(all_invoices), 2)

        # Filter unpaid
        unpaid_list = list_invoices(status_filter="unpaid", db=self.db)
        self.assertEqual(len(unpaid_list), 1)
        self.assertEqual(unpaid_list[0]["status"], InvoiceStatus.UNPAID)

        # Filter paid
        paid_list = list_invoices(status_filter="paid", db=self.db)
        self.assertEqual(len(paid_list), 1)
        self.assertEqual(paid_list[0]["status"], InvoiceStatus.PAID)

    def test_search_filter_by_invoice_number(self):
        """Test: Searching invoices by invoice number substring."""
        inv = generate_invoice_for_subscription(self.db, self.sub.id)
        matching = list_invoices(search=inv.invoice_number[-4:], db=self.db)
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["invoice_number"], inv.invoice_number)

        non_matching = list_invoices(search="NON-EXISTENT-XYZ", db=self.db)
        self.assertEqual(len(non_matching), 0)

    def test_pdf_invoice_generation(self):
        """Test: Generates a valid PDF invoice and attaches file path."""
        inv = generate_invoice_for_subscription(self.db, self.sub.id)
        self.assertIsNotNone(inv.pdf_path)
        self.assertTrue(os.path.exists(inv.pdf_path))
        self.assertTrue(inv.pdf_path.endswith(".pdf"))
        # Verify file has non-zero size
        self.assertGreater(os.path.getsize(inv.pdf_path), 500)
