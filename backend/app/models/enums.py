import enum

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class BillingInterval(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class BillingCycleStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    PAID = "paid"
    UNPAID = "unpaid"
    VOID = "void"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class EntityType(str, enum.Enum):
    PLAN = "plan"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"
    PAYMENT = "payment"

class CancellationTiming(str, enum.Enum):
    IMMEDIATE = "immediate"
    END_OF_CYCLE = "end_of_cycle"

class LineItemType(str, enum.Enum):
    PLAN_FEE = "plan_fee"
    PRORATION_CREDIT = "proration_credit"
    PRORATION_DEBIT = "proration_debit"
    TAX = "tax"
    USAGE = "usage"
