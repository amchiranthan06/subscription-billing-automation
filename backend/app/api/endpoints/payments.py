from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Payment, Invoice, Customer
from app.models.enums import PaymentStatus
from app.schemas.schemas import PaymentProcessRequest, PaymentProcessResponse, PaymentListItem
from app.services.payment import process_mock_payment

router = APIRouter(prefix="/payments", tags=["Payments (Milestone 2 - Task 3)"])


def _format_payment_list_item(p: Payment) -> dict:
    inv_num = p.invoice.invoice_number if p.invoice else None
    cust_name = (
        p.invoice.customer.name
        if p.invoice and p.invoice.customer
        else (p.customer.name if p.customer else None)
    )

    return {
        "id": p.id,
        "payment_reference": p.payment_reference,
        "invoice_id": p.invoice_id,
        "invoice_number": inv_num,
        "customer_name": cust_name,
        "amount": p.amount,
        "payment_method": p.payment_method,
        "status": p.status,
        "payment_date": p.payment_date,
        "created_at": p.created_at
    }


@router.post("/process", response_model=PaymentProcessResponse, status_code=status.HTTP_201_CREATED)
def process_payment_endpoint(
    payload: PaymentProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Milestone 2 - Task 3: Process payment via Mock Payment Gateway.
    - Decides success (80%) vs failure (20%) or uses optional force_status.
    - Creates a Payment record with unique transaction ID (TXN-...).
    - Dispatches webhook event to update Invoice and Subscription states.
    """
    try:
        result = process_mock_payment(
            db=db,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            payment_method=payload.payment_method or "credit_card",
            force_status=payload.force_status
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment processing failed: {str(e)}")


@router.get("", response_model=list[PaymentListItem])
def list_payments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: success, failed, refunded, pending"),
    search: Optional[str] = Query(None, description="Search by transaction reference or invoice number"),
    db: Session = Depends(get_db)
):
    """
    Lists payment transactions with optional status filter and search.
    """
    query = db.query(Payment).join(Payment.invoice, isouter=True)

    if status_filter and isinstance(status_filter, str):
        clean_status = status_filter.strip().lower()
        if clean_status in [s.value for s in PaymentStatus]:
            query = query.filter(Payment.status == PaymentStatus(clean_status))

    if search and isinstance(search, str):
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Payment.payment_reference.ilike(term),
                Invoice.invoice_number.ilike(term)
            )
        )

    payments = query.order_by(Payment.created_at.desc()).all()
    return [_format_payment_list_item(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentListItem)
def get_payment_detail(payment_id: str, db: Session = Depends(get_db)):
    """
    Get detailed payment transaction record by ID.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{payment_id}' not found.")
    return _format_payment_list_item(payment)
