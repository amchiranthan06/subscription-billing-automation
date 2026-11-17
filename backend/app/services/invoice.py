import os
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Invoice, InvoiceLineItem, Subscription, Customer, Plan, BillingCycle
from app.models.enums import InvoiceStatus, LineItemType, SubscriptionStatus
from app.services.audit import create_audit_log

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

INVOICE_PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "invoices_pdf")
os.makedirs(INVOICE_PDF_DIR, exist_ok=True)


def generate_unique_invoice_number(db: Session) -> str:
    """
    Generates a unique invoice number in format: INV-YYYYMM-XXXX
    e.g., INV-202611-0001
    """
    now = datetime.now(timezone.utc)
    prefix = f"INV-{now.strftime('%Y%m')}-"

    # Find highest sequence for current year-month
    existing_invoices = (
        db.query(Invoice.invoice_number)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .all()
    )

    max_seq = 0
    for (inv_num,) in existing_invoices:
        suffix = inv_num[len(prefix):]
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))

    new_seq = max_seq + 1
    invoice_number = f"{prefix}{new_seq:04d}"

    # Safety check against collision
    while db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first():
        new_seq += 1
        invoice_number = f"{prefix}{new_seq:04d}"

    return invoice_number


def calculate_invoice_financials(
    subtotal: Decimal,
    tax_rate: Decimal = Decimal("0.10")
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calculates subtotal, tax amount, and total amount rounded to 2 decimal places.
    Default tax rate is 10% (0.10).
    """
    subtotal_val = round(Decimal(str(subtotal)), 2)
    tax_val = round(subtotal_val * Decimal(str(tax_rate)), 2)
    total_val = subtotal_val + tax_val
    return subtotal_val, tax_val, total_val


def generate_invoice_pdf(invoice: Invoice, output_path: Optional[str] = None) -> str:
    """
    Generates a professional, branded PDF invoice using ReportLab.
    Saves file to output_path and returns the file path.
    """
    if not output_path:
        filename = f"{invoice.invoice_number}.pdf"
        output_path = os.path.join(INVOICE_PDF_DIR, filename)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    story = []

    # Title & Header
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#4F46E5"),
        fontName="Helvetica-Bold"
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B")
    )
    story.append(Paragraph("BillFlow Subscription Billing System", title_style))
    story.append(Paragraph("Creation of Subscription Billing Automation System using Recurring Revenue Model", subtitle_style))
    story.append(Spacer(1, 15))

    # Two column info table (Invoice Details & Customer Details)
    customer_name = invoice.customer.name if invoice.customer else "N/A"
    customer_email = invoice.customer.email if invoice.customer else "N/A"
    issue_date_str = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "N/A"
    due_date_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"
    status_str = invoice.status.value.upper() if hasattr(invoice.status, "value") else str(invoice.status).upper()

    status_color = colors.HexColor("#10B981") if status_str == "PAID" else colors.HexColor("#EF4444")

    details_data = [
        [
            Paragraph(f"<b>Billed To:</b><br/>{customer_name}<br/>{customer_email}", styles['Normal']),
            Paragraph(
                f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                f"<b>Issue Date:</b> {issue_date_str}<br/>"
                f"<b>Due Date:</b> {due_date_str}<br/>"
                f"<b>Status:</b> <font color='{status_color.hexval()}'><b>{status_str}</b></font>",
                styles['Normal']
            )
        ]
    ]

    details_table = Table(details_data, colWidths=[3.5 * inch, 3.5 * inch])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # Line Items Table
    table_data = [
        ["Item Description", "Type", "Amount (USD)"]
    ]

    if invoice.line_items:
        for item in invoice.line_items:
            type_label = item.line_item_type.value if hasattr(item.line_item_type, "value") else str(item.line_item_type)
            table_data.append([
                item.description,
                type_label.replace("_", " ").title(),
                f"${item.amount:.2f}"
            ])
    else:
        table_data.append(["Subscription Recurring Plan Fee", "Plan Fee", f"${invoice.subtotal:.2f}"])

    # Financial Summary Rows
    table_data.append(["", "Subtotal:", f"${invoice.subtotal:.2f}"])
    table_data.append(["", "Tax (10%):", f"${invoice.tax_amount:.2f}"])
    table_data.append(["", "Total Amount:", f"${invoice.total_amount:.2f}"])

    items_table = Table(table_data, colWidths=[4.2 * inch, 1.6 * inch, 1.4 * inch])
    items_table.setStyle(TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Body style
        ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, -4), 0.5, colors.HexColor("#E2E8F0")),
        # Summary rows style
        ('FONTNAME', (1, -3), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (1, -3), (-1, -3), 1, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (1, -1), (-1, -1), colors.HexColor("#EEF2FF")),
        ('TEXTCOLOR', (1, -1), (-1, -1), colors.HexColor("#4F46E5")),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 25))

    # Footer note
    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#94A3B8"),
        alignment=1 # Center
    )
    story.append(Paragraph("Thank you for your business! This is an automatically generated electronic invoice.", footer_style))

    doc.build(story)
    return output_path


def generate_invoice_for_subscription(
    db: Session,
    subscription_id: str,
    billing_cycle_id: Optional[str] = None,
    tax_rate: Decimal = Decimal("0.10"),
    due_days: int = 14
) -> Invoice:
    """
    Generates an itemized invoice for an active/trial subscription.
    - Computes Subtotal, Tax (default 10%), and Total.
    - Creates Invoice and InvoiceLineItem records.
    - Saves PDF invoice via ReportLab.
    - Creates immutable audit log entry.
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise ValueError(f"Subscription '{subscription_id}' not found.")

    customer = subscription.customer
    if not customer:
        raise ValueError(f"Customer for subscription '{subscription_id}' not found.")

    plan = subscription.plan
    if not plan:
        raise ValueError(f"Plan for subscription '{subscription_id}' not found.")

    # If billing_cycle_id is provided, verify it exists and belongs to this subscription
    billing_cycle = None
    if billing_cycle_id:
        billing_cycle = (
            db.query(BillingCycle)
            .filter(BillingCycle.id == billing_cycle_id, BillingCycle.subscription_id == subscription_id)
            .first()
        )
        if not billing_cycle:
            raise ValueError(f"Billing cycle '{billing_cycle_id}' does not belong to subscription '{subscription_id}'.")

        # Check if an invoice was already generated for this billing cycle
        existing = db.query(Invoice).filter(Invoice.billing_cycle_id == billing_cycle_id).first()
        if existing:
            return existing
    else:
        # Check if there is an active/pending billing cycle for this subscription
        billing_cycle = (
            db.query(BillingCycle)
            .filter(BillingCycle.subscription_id == subscription_id)
            .order_by(BillingCycle.cycle_index.desc())
            .first()
        )

    # Calculate financial amounts
    base_fee = Decimal(str(plan.price))
    subtotal, tax_amount, total_amount = calculate_invoice_financials(base_fee, tax_rate=tax_rate)

    now = datetime.now(timezone.utc)
    due_date = now + timedelta(days=due_days)
    inv_number = generate_unique_invoice_number(db)

    # Create Invoice record
    invoice = Invoice(
        invoice_number=inv_number,
        subscription_id=subscription.id,
        customer_id=customer.id,
        billing_cycle_id=billing_cycle.id if billing_cycle else None,
        invoice_date=now,
        due_date=due_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=InvoiceStatus.UNPAID,
        currency="USD"
    )
    db.add(invoice)
    db.flush()

    # Create Line Item (Plan Fee)
    interval_label = plan.billing_interval.value if hasattr(plan.billing_interval, "value") else str(plan.billing_interval)
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description=f"{plan.name} ({interval_label.capitalize()}) - Subscription Recurring Fee",
        amount=subtotal,
        line_item_type=LineItemType.PLAN_FEE,
        metadata_json={
            "plan_id": plan.id,
            "plan_name": plan.name,
            "billing_interval": interval_label,
            "tax_rate": float(tax_rate)
        }
    )
    db.add(line_item)
    db.flush()

    # Generate and attach PDF
    try:
        pdf_path = generate_invoice_pdf(invoice)
        invoice.pdf_path = pdf_path
    except Exception as e:
        # Don't fail the transaction if PDF generation runs into an IO quirk
        invoice.pdf_path = None

    db.commit()
    db.refresh(invoice)

    # Log to audit trail
    create_audit_log(
        db=db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="invoice_generated",
        old_value=None,
        new_value={
            "invoice_number": invoice.invoice_number,
            "customer_id": customer.id,
            "subscription_id": subscription.id,
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "status": invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status)
        },
        performed_by="system",
        customer_id=customer.id,
        subscription_id=subscription.id
    )

    return invoice
