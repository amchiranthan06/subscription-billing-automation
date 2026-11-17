"""Request and response shapes for the API (Pydantic models)."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import (
    BillingCycleStatus,
    BillingInterval,
    PlanStatus,
    SubscriptionStatus,
)


# ----------------------------------------------------------------- plans
class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    billing_interval: BillingInterval
    trial_period_days: int = Field(default=0, ge=0, le=365)
    features: dict[str, Any] = Field(default_factory=dict)  # feature entitlements

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return value.upper()


class PlanUpdate(BaseModel):
    """Only these fields can be edited. Billing interval and currency are fixed after creation."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    trial_period_days: Optional[int] = Field(default=None, ge=0, le=365)
    features: Optional[dict[str, Any]] = None


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    price: Decimal
    currency: str
    billing_interval: BillingInterval
    trial_period_days: int
    features: dict[str, Any]
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]


# ------------------------------------------------------------- customers
class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    country: str = Field(default="IN", min_length=2, max_length=2)

    @field_validator("country")
    @classmethod
    def country_upper(cls, value: str) -> str:
        return value.upper()


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    country: str
    created_at: datetime


# --------------------------------------------------------- subscriptions
class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_trial: bool = True  # if the plan has a trial period, begin with the trial


class ChangePlanRequest(BaseModel):
    new_plan_id: int
    effective: Literal["immediate", "next_cycle"] = "immediate"


class CancelRequest(BaseModel):
    timing: Literal["immediate", "end_of_cycle"] = "immediate"
    reason: Optional[str] = Field(default=None, max_length=255)


class TransitionRequest(BaseModel):
    to_status: SubscriptionStatus
    reason: Optional[str] = Field(default=None, max_length=255)


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    plan_id: int
    pending_plan_id: Optional[int]
    status: SubscriptionStatus
    trial_started_at: Optional[datetime]
    trial_end: Optional[datetime]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    is_paused: bool
    paused_at: Optional[datetime]
    cancel_at_period_end: bool
    status_changed_at: Optional[datetime]
    activated_at: Optional[datetime]
    past_due_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------- billing
class BillingCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    plan_id: int
    cycle_number: int
    period_start: datetime
    period_end: datetime
    status: BillingCycleStatus
    invoice_job_triggered_at: Optional[datetime]
    created_at: datetime


class ScanRequest(BaseModel):
    """Optional. 'as_of' lets you pretend it is a later date, to test renewals without waiting."""

    as_of: Optional[datetime] = None


class ScanResultOut(BaseModel):
    as_of: datetime
    trials_converted: int
    renewals_created: int
    cancellations_applied: int
    invoice_jobs_dispatched: int
    errors: int


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: Optional[int]
    subscription_id: Optional[int]
    entity_type: str
    entity_id: Optional[int]
    action: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    actor: str
    created_at: datetime
