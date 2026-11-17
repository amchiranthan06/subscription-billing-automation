import os
from typing import Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Invoice, Subscription, Customer
from app.models.enums import InvoiceStatus
from app.schemas.schemas import InvoiceResponse, InvoiceGenerateRequest
from app.services.invoice import (
    generate_invoice_for_subscription,
    generate_invoice_pdf
)

router = APIRouter(prefix="/invoices", tags=["Invoices (Milestone 2 - Task 1)"])


def _format_invoice_response(inv: Invoice) -> dict:
    """Helper to populate customer and plan names for rich API/UI responses."""
    customer_name = inv.customer.name if inv.customer else None
    customer_email = inv.customer.email if inv.customer else None
    plan_name = (
        inv.subscription.plan.name
        if inv.subscription and inv.subscription.plan
        else None
    )

    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "subscription_id": inv.subscription_id,
        "customer_id": inv.customer_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "plan_name": plan_name,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "subtotal": inv.subtotal,
        "tax_amount": inv.tax_amount,
        "total_amount": inv.total_amount,
        "status": inv.status,
        "currency": inv.currency,
        "paid_at": inv.paid_at,
        "pdf_path": inv.pdf_path,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "line_items": inv.line_items or []
    }


@router.post("/generate", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def generate_invoice(
    payload: InvoiceGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically generate an itemized invoice for an active subscription.
    Computes subtotal, tax (default 10%), total, sets status to unpaid,
    attaches line items, and generates a downloadable PDF.
    """
    try:
        invoice = generate_invoice_for_subscription(
            db=db,
            subscription_id=payload.subscription_id,
            billing_cycle_id=payload.billing_cycle_id,
            tax_rate=payload.tax_rate or Decimal("0.10")
        )
        return _format_invoice_response(invoice)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: paid or unpaid"),
    search: Optional[str] = Query(None, description="Search by invoice number, customer name, or email"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    subscription_id: Optional[str] = Query(None, description="Filter by subscription ID"),
    start_date: Optional[str] = Query(None, description="Filter invoices on or after YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter invoices on or before YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    List invoices with support for status filtering (paid/unpaid),
    search filtering (by invoice number or customer), and date range filtering.
    """
    query = db.query(Invoice).join(Invoice.customer, isouter=True)

    # Status filter
    if status_filter and isinstance(status_filter, str):
        clean_status = status_filter.strip().lower()
        if clean_status in [s.value for s in InvoiceStatus]:
            query = query.filter(Invoice.status == InvoiceStatus(clean_status))

    # Customer or subscription filter
    if customer_id and isinstance(customer_id, str):
        query = query.filter(Invoice.customer_id == customer_id.strip())
    if subscription_id and isinstance(subscription_id, str):
        query = query.filter(Invoice.subscription_id == subscription_id.strip())

    # Search filter (invoice number or customer name/email)
    if search and isinstance(search, str):
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(search_term),
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )

    # Date range filters
    if start_date and isinstance(start_date, str):
        try:
            sd = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date >= sd)
        except ValueError:
            pass

    if end_date and isinstance(end_date, str):
        try:
            ed = datetime.strptime(end_date.strip(), "%Y-%m-%d")
            # Include entire end date day
            query = query.filter(Invoice.invoice_date <= ed.replace(hour=23, minute=59, second=59))
        except ValueError:
            pass

    invoices = query.order_by(Invoice.created_at.desc()).all()
    return [_format_invoice_response(inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """
    Get detailed invoice by ID, including customer, plan, and itemized line items.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found."
        )
    return _format_invoice_response(invoice)


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: str, db: Session = Depends(get_db)):
    """
    Download invoice as a formatted PDF file.
    If the PDF does not exist on disk, it is dynamically generated on-the-fly.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found."
        )

    pdf_path = invoice.pdf_path
    if not pdf_path or not os.path.exists(pdf_path):
        # Regenerate PDF
        pdf_path = generate_invoice_pdf(invoice)
        invoice.pdf_path = pdf_path
        db.commit()

    filename = f"{invoice.invoice_number}.pdf"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )
