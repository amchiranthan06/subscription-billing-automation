from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.models.enums import (
    SubscriptionStatus, BillingInterval, InvoiceStatus,
    PaymentStatus, CancellationTiming, LineItemType
)

# ----------------- CUSTOMER SCHEMAS -----------------
class CustomerBase(BaseModel):
    name: str = Field(..., example="Acme Corp")
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", example="billing@acmecorp.com")
    company_name: Optional[str] = Field(default=None, example="Acme Inc.")
    country: str = Field(default="US", example="US")
    currency: str = Field(default="USD", example="USD")

class CustomerCreate(CustomerBase):
    payment_method_id: Optional[str] = "pm_mock_card_valid"

class CustomerResponse(CustomerBase):
    id: str
    payment_method_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- PLAN SCHEMAS -----------------
class PlanBase(BaseModel):
    name: str = Field(..., example="Pro Plan")
    code: str = Field(..., example="pro")
    description: Optional[str] = "For growing teams and scaling startups"
    price: Decimal = Field(..., gt=0, example=29.00)
    currency: str = Field(default="USD")
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    trial_days: int = Field(default=14, ge=0)
    features: Optional[dict[str, Any]] = Field(default_factory=dict)
    feature_entitlements: Optional[dict[str, Any]] = Field(default_factory=dict)

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    feature_entitlements: Optional[dict[str, Any]] = None

class PlanResponse(PlanBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- SUBSCRIPTION SCHEMAS -----------------
class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: str
    start_with_trial: bool = True
    custom_trial_days: Optional[int] = None

class SubscriptionChangePlan(BaseModel):
    new_plan_id: str
    prorate: bool = True

class SubscriptionCancel(BaseModel):
    timing: CancellationTiming = CancellationTiming.IMMEDIATE
    reason: Optional[str] = "Customer requested cancellation"

class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    plan: Optional[PlanResponse] = None

    class Config:
        from_attributes = True

# ----------------- BILLING CYCLE SCHEMAS -----------------
class BillingCycleResponse(BaseModel):
    id: str
    subscription_id: str
    cycle_start_date: datetime
    cycle_end_date: datetime
    renewal_date: datetime
    status: str
    cycle_index: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- INVOICE & LINE ITEM SCHEMAS -----------------
class InvoiceLineItemResponse(BaseModel):
    id: str
    description: str
    amount: Decimal
    line_item_type: LineItemType
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    subscription_id: Optional[str] = None
    customer_id: str
    invoice_date: datetime
    due_date: datetime
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    currency: str = "USD"
    paid_at: Optional[datetime] = None
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    line_items: list[InvoiceLineItemResponse] = []

    class Config:
        from_attributes = True

# ----------------- PAYMENT SCHEMAS -----------------
class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    payment_reference: Optional[str] = None
    amount: Decimal
    payment_method: str
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- AUDIT LOG SCHEMAS -----------------
class AuditLogResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    performed_by: str
    created_at: datetime

    class Config:
        from_attributes = True
