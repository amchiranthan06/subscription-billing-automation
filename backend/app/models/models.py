import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    SubscriptionStatus, BillingInterval, InvoiceStatus,
    PaymentStatus, CancellationTiming, LineItemType
)

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    company_name = Column(String(150), nullable=True)
    country = Column(String(50), default="US")
    currency = Column(String(10), default="USD")
    payment_method_id = Column(String(100), nullable=True, default="pm_mock_card_default")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer")
    audit_logs = relationship("AuditLog", back_populates="customer")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "starter", "pro", "enterprise"
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    billing_interval = Column(SQLEnum(BillingInterval), default=BillingInterval.MONTHLY, nullable=False)
    trial_days = Column(Integer, default=14)
    features = Column(JSON, default=dict)
    feature_entitlements = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False, index=True)
    
    current_period_start = Column(DateTime, nullable=False, default=utc_now)
    current_period_end = Column(DateTime, nullable=False)
    
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
    retries = relationship("FailedPaymentRetry", back_populates="subscription")

class BillingCycle(Base):
    __tablename__ = "billing_cycles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False, index=True)
    cycle_index = Column(Integer, default=1, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(30), default="scheduled") # scheduled, processing, completed, failed
    created_at = Column(DateTime, default=utc_now)

    subscription = relationship("Subscription", back_populates="billing_cycles")
    invoices = relationship("Invoice", back_populates="billing_cycle")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True, index=True)
    billing_cycle_id = Column(String(36), ForeignKey("billing_cycles.id"), nullable=True)
    
    subtotal = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    
    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    pdf_path = Column(String(255), nullable=True)
    
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

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    gateway_transaction_id = Column(String(100), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    invoice = relationship("Invoice", back_populates="payments")

class FailedPaymentRetry(Base):
    __tablename__ = "failed_payment_retries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False) # 1, 2, or 3
    scheduled_for = Column(DateTime, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="scheduled") # scheduled, successful, failed, cancelled
    error_message = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    subscription = relationship("Subscription", back_populates="retries")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True) # e.g. "subscription.created", "subscription.upgraded", "payment.failed"
    old_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    actor = Column(String(100), default="system")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    customer = relationship("Customer", back_populates="audit_logs")
    subscription = relationship("Subscription", back_populates="audit_logs")
