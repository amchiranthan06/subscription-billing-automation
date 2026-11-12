import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    SubscriptionStatus, BillingInterval, BillingCycleStatus,
    InvoiceStatus, PaymentStatus, LineItemType
)

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# ----------------- 0. USERS MODEL (TASK 3) -----------------
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False) # admin, user
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

# ----------------- 1. PLANS MODEL -----------------
class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    billing_interval = Column(SQLEnum(BillingInterval), default=BillingInterval.MONTHLY, nullable=False)
    trial_days = Column(Integer, default=14)
    features = Column(JSON, default=dict) # Features
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subscriptions = relationship("Subscription", back_populates="plan")

# ----------------- 2. CUSTOMERS MODEL -----------------
class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    company_name = Column(String(150), nullable=True) # Company_name
    country = Column(String(50), default="US")
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer")
    audit_logs = relationship("AuditLog", back_populates="customer")

# ----------------- 3. SUBSCRIPTIONS MODEL -----------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False, index=True)
    
    start_date = Column(DateTime, nullable=False, default=utc_now) # start_date
    end_date = Column(DateTime, nullable=False)                   # End_date
    
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    billing_cycles = relationship("BillingCycle", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription")
    audit_logs = relationship("AuditLog", back_populates="subscription")

# ----------------- 4. BILLING CYCLES MODEL -----------------
class BillingCycle(Base):
    __tablename__ = "billing_cycles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False, index=True)
    cycle_start_date = Column(DateTime, nullable=False) # cycle_start_date
    cycle_end_date = Column(DateTime, nullable=False)   # cycle_end_date
    renewal_date = Column(DateTime, nullable=False)     # renewal_date
    status = Column(SQLEnum(BillingCycleStatus), default=BillingCycleStatus.PENDING, nullable=False) # pending/completed
    cycle_index = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subscription = relationship("Subscription", back_populates="billing_cycles")
    invoices = relationship("Invoice", back_populates="billing_cycle")

# ----------------- 5. INVOICES MODEL -----------------
class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False) # invoice_number
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True, index=True) # subscription_id
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True) # customer_id
    invoice_date = Column(DateTime, default=utc_now, nullable=False) # invoice_date
    due_date = Column(DateTime, nullable=False) # due_date
    
    subtotal = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False) # Total_amount
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True) # draft/paid/unpaid/void
    
    currency = Column(String(10), default="USD")
    paid_at = Column(DateTime, nullable=True)
    pdf_path = Column(String(255), nullable=True)
    billing_cycle_id = Column(String(36), ForeignKey("billing_cycles.id"), nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    billing_cycle = relationship("BillingCycle", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    line_item_type = Column(SQLEnum(LineItemType), default=LineItemType.PLAN_FEE, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    invoice = relationship("Invoice", back_populates="line_items")

# ----------------- 6. PAYMENTS MODEL -----------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True) # invoice_id
    payment_reference = Column(String(100), unique=True, index=True, default=generate_uuid) # payment_reference
    amount = Column(Numeric(10, 2), nullable=False) # amount
    payment_method = Column(String(50), default="credit_card", nullable=False) # payment_method
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True) # pending/success/failed/refunded
    payment_date = Column(DateTime, nullable=True) # payment_date
    
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    currency = Column(String(10), default="USD")
    failure_reason = Column(String(255), nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now) # Updated_at

    invoice = relationship("Invoice", back_populates="payments")

# ----------------- 7. AUDIT LOGS MODEL -----------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True) # entity_type (plan/subscription/invoice/payment)
    entity_id = Column(String(50), nullable=False, index=True)   # entity_id
    action = Column(String(100), nullable=False)                 # action
    old_value = Column(JSON, nullable=True)                      # old_value
    new_value = Column(JSON, nullable=True)                      # new_value
    performed_by = Column(String(100), default="system", nullable=False) # performed_by
    created_at = Column(DateTime, default=utc_now, index=True)   # created_at
    
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)

    customer = relationship("Customer", back_populates="audit_logs")
    subscription = relationship("Subscription", back_populates="audit_logs")
