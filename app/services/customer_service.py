"""Customer management: create, get, list."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import log_event
from app.errors import ConflictError, NotFoundError
from app.models import Customer
from app.schemas import CustomerCreate


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise NotFoundError(f"Customer {customer_id} not found")
    return customer


def list_customers(db: Session) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.id)).all())


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    email = data.email.lower()
    if db.scalar(select(Customer.id).where(Customer.email == email)) is not None:
        raise ConflictError(f"A customer with email '{email}' already exists")

    customer = Customer(name=data.name, email=email, country=data.country)
    db.add(customer)
    db.flush()
    log_event(
        db,
        action="customer.created",
        entity_type="customer",
        entity_id=customer.id,
        customer_id=customer.id,
        new_value={"name": customer.name, "email": customer.email, "country": customer.country},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"A customer with email '{email}' already exists")
    db.refresh(customer)
    return customer
