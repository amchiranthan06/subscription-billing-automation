from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import PaymentWebhookPayload
from app.services.payment import handle_payment_webhook

router = APIRouter(prefix="/webhooks", tags=["Webhooks (Milestone 2 - Task 3)"])


@router.post("/payment", status_code=status.HTTP_200_OK)
def receive_payment_webhook(
    payload: PaymentWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Milestone 2 - Task 3: Payment Webhook Handler.
    Receives events:
    - 'payment_success': marks Invoice paid, verifies subscription is active
    - 'payment_failed': moves Subscription to past_due, logs failure
    - 'payment_refunded': marks Invoice void and Payment refunded
    """
    try:
        outcome = handle_payment_webhook(
            db=db,
            event=payload.event,
            invoice_id=payload.invoice_id,
            payment_reference=payload.payment_reference,
            amount=payload.amount,
            failure_reason=payload.failure_reason
        )
        return outcome
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Webhook processing error: {str(e)}")
