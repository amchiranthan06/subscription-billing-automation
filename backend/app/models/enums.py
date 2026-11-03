import enum

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class BillingInterval(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    PAST_DUE = "past_due"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"

class CancellationTiming(str, enum.Enum):
    IMMEDIATE = "immediate"
    END_OF_CYCLE = "end_of_cycle"

class LineItemType(str, enum.Enum):
    PLAN_FEE = "plan_fee"
    PRORATION_CREDIT = "proration_credit"
    PRORATION_DEBIT = "proration_debit"
    TAX = "tax"
    USAGE = "usage"
