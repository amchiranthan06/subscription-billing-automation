from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Customer, AuditLog
from app.schemas.schemas import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customer Management APIs (Task 6)"])

# 1. CREATE CUSTOMER: POST /customers
@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    """Registers a new SaaS customer account."""
    existing = db.query(Customer).filter(Customer.email == customer_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with email '{customer_in.email}' already exists."
        )
    
    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
        company_name=customer_in.company_name,
        country=customer_in.country,
        currency=customer_in.currency
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    audit = AuditLog(
        entity_type="customer",
        entity_id=customer.id,
        action="customer_created",
        old_value=None,
        new_value={"email": customer.email, "name": customer.name, "company_name": customer.company_name},
        performed_by="system",
        customer_id=customer.id
    )
    db.add(audit)
    db.commit()

    return customer

# 2. LIST CUSTOMERS: GET /customers
@router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    """Retrieves all registered customers."""
    return db.query(Customer).order_by(Customer.created_at.desc()).all()

# 3. GET SINGLE CUSTOMER: GET /customers/{id}
@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Fetches a single customer by their ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer

# 4. UPDATE CUSTOMER: PUT /customers/{id}
@router.put("/{customer_id}", response_model=CustomerResponse)
@router.patch("/{customer_id}", response_model=CustomerResponse, include_in_schema=False)
def update_customer(customer_id: str, customer_update: CustomerUpdate, db: Session = Depends(get_db)):
    """Updates an existing customer profile."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # If updating email, check for uniqueness
    if customer_update.email and customer_update.email != customer.email:
        email_taken = db.query(Customer).filter(
            Customer.email == customer_update.email,
            Customer.id != customer_id
        ).first()
        if email_taken:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{customer_update.email}' is already in use by another customer."
            )

    old_data = {
        "name": customer.name,
        "email": customer.email,
        "company_name": customer.company_name
    }

    update_dict = customer_update.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(customer, field, value)

    audit = AuditLog(
        entity_type="customer",
        entity_id=customer.id,
        action="customer_updated",
        old_value=old_data,
        new_value={
            "name": customer.name,
            "email": customer.email,
            "company_name": customer.company_name
        },
        performed_by="system",
        customer_id=customer.id
    )
    db.add(audit)
    db.commit()
    db.refresh(customer)

    return customer
