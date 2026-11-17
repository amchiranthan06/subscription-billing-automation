"""All enum types used by the database and the API."""
import enum


class BillingInterval(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"


class BillingCycleStatus(str, enum.Enum):
    PENDING = "pending"      # cycle created, invoice not generated yet
    INVOICED = "invoiced"    # set by the invoice engine (Milestone 2)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
