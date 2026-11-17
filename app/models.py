"""Database tables (SQLAlchemy models).

Tables: plans, customers, subscriptions, billing_cycles, invoices, payments, audit_logs.
Status columns use real PostgreSQL ENUM types.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.database import Base
from app.enums import (
    BillingCycleStatus,
    BillingInterval,
    InvoiceStatus,
    PaymentStatus,
    PlanStatus,
    SubscriptionStatus,
)
from app.utils import utcnow


class UTCDateTime(TypeDecorator):
    """Timezone-aware datetime that is always stored and returned as UTC.

    PostgreSQL uses TIMESTAMPTZ. This wrapper also makes SQLite (used by the tests)
    return timezone-aware values, so comparisons never mix naive and aware datetimes.
    """

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def pg_enum(enum_cls, name: str) -> SAEnum:
    """Create a database enum that stores the lowercase values ('trial', 'active', ...)."""
    return SAEnum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


# JSONB on PostgreSQL, plain JSON elsewhere (SQLite in tests).
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_plans_price_non_negative"),
        CheckConstraint("trial_period_days >= 0", name="ck_plans_trial_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    billing_interval: Mapped[BillingInterval] = mapped_column(
        pg_enum(BillingInterval, "billing_interval"), nullable=False
    )
    trial_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)  # feature entitlements
    status: Mapped[PlanStatus] = mapped_column(
        pg_enum(PlanStatus, "plan_status"), nullable=False, default=PlanStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)
    archived_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="IN")  # used for tax later
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_status_period_end", "status", "current_period_end"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False, index=True)
    pending_plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plans.id"), nullable=True)

    status: Mapped[SubscriptionStatus] = mapped_column(
        pg_enum(SubscriptionStatus, "subscription_status"),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
    )

    # Trial window
    trial_started_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    # Current billing period (during a trial it equals the trial window)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    # Pause / cancel flags
    is_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paused_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps for each state change
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    past_due_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)

    plan: Mapped["Plan"] = relationship("Plan", foreign_keys="Subscription.plan_id")
    pending_plan: Mapped[Optional["Plan"]] = relationship("Plan", foreign_keys="Subscription.pending_plan_id")


class BillingCycle(Base):
    """One row per billed period of a subscription. The scheduler creates these."""

    __tablename__ = "billing_cycles"
    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", name="uq_cycle_subscription_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    status: Mapped[BillingCycleStatus] = mapped_column(
        pg_enum(BillingCycleStatus, "billing_cycle_status"),
        nullable=False,
        default=BillingCycleStatus.PENDING,
    )
    invoice_job_triggered_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)


class Invoice(Base):
    """Table is created in Milestone 1; invoice generation logic comes in Milestone 2."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False, index=True)
    billing_cycle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("billing_cycles.id"), nullable=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        pg_enum(InvoiceStatus, "invoice_status"), nullable=False, default=InvoiceStatus.DRAFT
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_items: Mapped[list] = mapped_column(JSON_TYPE, nullable=False, default=list)
    issued_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)


class Payment(Base):
    """Table is created in Milestone 1; payment processing comes in Milestone 2."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, "payment_status"), nullable=False, default=PaymentStatus.PENDING
    )
    gateway_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)


class AuditLog(Base):
    """Append-only history of billing events (financial compliance)."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subscriptions.id"), nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_value: Mapped[Optional[dict]] = mapped_column(JSON_TYPE, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON_TYPE, nullable=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow, index=True)
