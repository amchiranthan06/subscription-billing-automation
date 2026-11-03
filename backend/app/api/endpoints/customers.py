from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Customer, AuditLog
from app.schemas.schemas import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter(Customer.email == customer_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with email '{customer_in.email}' already exists."
        )
    
    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
        country=customer_in.country,
        currency=customer_in.currency,
        payment_method_id=customer_in.payment_method_id or "pm_mock_card_valid"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    audit = AuditLog(
        customer_id=customer.id,
        event_type="customer.created",
        new_state={"email": customer.email, "name": customer.name},
        actor="system",
        description=f"Customer '{customer.name}' registered."
    )
    db.add(audit)
    db.commit()

    return customer

@router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.created_at.desc()).all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer
