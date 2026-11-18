from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Subscription, Plan, Invoice, InvoiceLineItem, Customer, BillingCycle
from app.models.enums import LineItemType, InvoiceStatus, SubscriptionStatus
from app.services.audit import create_audit_log
from app.services.invoice import generate_unique_invoice_number, generate_invoice_pdf


def calculate_proration(
    start_date: datetime,
    end_date: datetime,
    current_price: Decimal,
    new_price: Decimal,
    change_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Computes mathematically fair proration for mid-cycle plan changes:
    - total_days: length of current billing cycle
    - remaining_days: days left from change_date to end_date
    - unused_credit: credit for unused portion of old plan
    - new_charge: prorated cost for new plan for remaining period
    - net_amount_due: new_charge - unused_credit
    """
    if change_date is None:
        change_date = datetime.now(timezone.utc)

    # Ensure timezone awareness compatibility
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if change_date.tzinfo is None:
        change_date = change_date.replace(tzinfo=timezone.utc)

    # Clamp change_date between start_date and end_date
    if change_date < start_date:
        change_date = start_date
    if change_date > end_date:
        change_date = end_date

    total_seconds = max(1, (end_date - start_date).total_seconds())
    remaining_seconds = max(0, (end_date - change_date).total_seconds())

    # Ratio of remaining period
    ratio = Decimal(str(remaining_seconds)) / Decimal(str(total_seconds))

    total_days = max(1, (end_date.date() - start_date.date()).days)
    remaining_days = max(0, (end_date.date() - change_date.date()).days)

    unused_credit = round(Decimal(str(current_price)) * ratio, 2)
    new_charge = round(Decimal(str(new_price)) * ratio, 2)
    net_amount_due = round(new_charge - unused_credit, 2)

    return {
        "total_days": total_days,
        "remaining_days": remaining_days,
        "remaining_ratio": float(round(ratio, 4)),
        "unused_credit": unused_credit,
        "new_charge": new_charge,
        "net_amount_due": net_amount_due,
        "is_upgrade": net_amount_due > 0,
        "is_downgrade": net_amount_due < 0
    }


def preview_plan_change(
    db: Session,
    subscription_id: str,
    new_plan_id: str
) -> Dict[str, Any]:
    """
    Returns live proration preview without persisting any database changes.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise ValueError(f"Subscription '{subscription_id}' not found.")

    if sub.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise ValueError(f"Cannot change plan for subscription in '{sub.status.value}' state.")

    current_plan = sub.plan
    new_plan = db.query(Plan).filter(Plan.id == new_plan_id).first()
    if not new_plan:
        raise ValueError(f"Target plan '{new_plan_id}' not found.")

    if not new_plan.is_active:
        raise ValueError(f"Target plan '{new_plan.name}' is inactive.")

    if current_plan.id == new_plan.id:
        raise ValueError("Subscription is already on this plan.")

    # Determine current cycle boundaries
    cycle = (
        db.query(BillingCycle)
        .filter(BillingCycle.subscription_id == sub.id)
        .order_by(BillingCycle.cycle_index.desc())
        .first()
    )

    start_date = cycle.cycle_start_date if cycle else sub.start_date
    end_date = cycle.cycle_end_date if cycle else sub.end_date

    proration_data = calculate_proration(
        start_date=start_date,
        end_date=end_date,
        current_price=Decimal(str(current_plan.price)),
        new_price=Decimal(str(new_plan.price))
    )

    return {
        "subscription_id": sub.id,
        "current_plan": {
            "id": current_plan.id,
            "name": current_plan.name,
            "price": float(current_plan.price),
            "billing_interval": current_plan.billing_interval.value
        },
        "new_plan": {
            "id": new_plan.id,
            "name": new_plan.name,
            "price": float(new_plan.price),
            "billing_interval": new_plan.billing_interval.value
        },
        "cycle_start_date": start_date,
        "cycle_end_date": end_date,
        "proration": proration_data
    }


def apply_plan_change_with_proration(
    db: Session,
    subscription_id: str,
    new_plan_id: str
) -> Dict[str, Any]:
    """
    Executes the plan change mid-cycle:
    1. Computes proration numbers.
    2. Updates subscription plan_id.
    3. Generates an adjustment Invoice with Line Items (Credit and Debit).
    4. Writes an immutable Audit Log entry.
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise ValueError(f"Subscription '{subscription_id}' not found.")

    if sub.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise ValueError(f"Cannot change plan for subscription in '{sub.status.value}' state.")

    old_plan = sub.plan
    new_plan = db.query(Plan).filter(Plan.id == new_plan_id).first()
    if not new_plan:
        raise ValueError(f"Target plan '{new_plan_id}' not found.")
    if not new_plan.is_active:
        raise ValueError(f"Target plan '{new_plan.name}' is inactive.")
    if old_plan.id == new_plan.id:
        raise ValueError("Subscription is already on this plan.")

    cycle = (
        db.query(BillingCycle)
        .filter(BillingCycle.subscription_id == sub.id)
        .order_by(BillingCycle.cycle_index.desc())
        .first()
    )

    start_date = cycle.cycle_start_date if cycle else sub.start_date
    end_date = cycle.cycle_end_date if cycle else sub.end_date
    now = datetime.now(timezone.utc)

    proration_data = calculate_proration(
        start_date=start_date,
        end_date=end_date,
        current_price=Decimal(str(old_plan.price)),
        new_price=Decimal(str(new_plan.price)),
        change_date=now
    )

    # 1. Update Subscription
    sub.plan_id = new_plan.id
    db.flush()

    # 2. Create Proration Adjustment Invoice
    unused_credit = proration_data["unused_credit"]
    new_charge = proration_data["new_charge"]
    net_due = proration_data["net_amount_due"]

    inv_number = generate_unique_invoice_number(db)
    subtotal = max(Decimal("0.00"), net_due)
    tax_amount = round(subtotal * Decimal("0.10"), 2)
    total_amount = subtotal + tax_amount

    invoice = Invoice(
        invoice_number=inv_number,
        subscription_id=sub.id,
        customer_id=sub.customer_id,
        billing_cycle_id=cycle.id if cycle else None,
        invoice_date=now,
        due_date=now,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=InvoiceStatus.PAID if net_due <= 0 else InvoiceStatus.UNPAID,
        currency="USD"
    )
    db.add(invoice)
    db.flush()

    # Line item 1: Unused Plan Credit
    credit_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description=f"Unused {old_plan.name} Credit ({proration_data['remaining_days']} days remaining)",
        amount=-unused_credit,
        line_item_type=LineItemType.PRORATION_CREDIT,
        metadata_json={
            "plan_id": old_plan.id,
            "plan_name": old_plan.name,
            "credit": float(unused_credit)
        }
    )
    db.add(credit_item)

    # Line item 2: New Plan Prorated Charge
    charge_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description=f"{new_plan.name} Prorated Charge ({proration_data['remaining_days']} days remaining)",
        amount=new_charge,
        line_item_type=LineItemType.PRORATION_DEBIT,
        metadata_json={
            "plan_id": new_plan.id,
            "plan_name": new_plan.name,
            "charge": float(new_charge)
        }
    )
    db.add(charge_item)
    db.flush()

    # Generate PDF for this adjustment
    try:
        pdf_path = generate_invoice_pdf(invoice)
        invoice.pdf_path = pdf_path
    except Exception:
        invoice.pdf_path = None

    db.commit()
    db.refresh(sub)
    db.refresh(invoice)

    # 3. Create Audit Log
    create_audit_log(
        db=db,
        entity_type="subscription",
        entity_id=sub.id,
        action="plan_changed",
        old_value={
            "plan_id": old_plan.id,
            "plan_name": old_plan.name,
            "price": float(old_plan.price)
        },
        new_value={
            "plan_id": new_plan.id,
            "plan_name": new_plan.name,
            "price": float(new_plan.price),
            "unused_credit": float(unused_credit),
            "new_charge": float(new_charge),
            "net_amount_due": float(net_due),
            "invoice_number": invoice.invoice_number
        },
        performed_by="customer",
        customer_id=sub.customer_id,
        subscription_id=sub.id
    )

    return {
        "subscription_id": sub.id,
        "old_plan": {
            "id": old_plan.id,
            "name": old_plan.name,
            "price": float(old_plan.price)
        },
        "new_plan": {
            "id": new_plan.id,
            "name": new_plan.name,
            "price": float(new_plan.price)
        },
        "proration": proration_data,
        "adjustment_invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "subtotal": float(invoice.subtotal),
            "tax_amount": float(invoice.tax_amount),
            "total_amount": float(invoice.total_amount),
            "status": invoice.status.value
        }
    }
