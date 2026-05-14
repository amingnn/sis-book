from sqlmodel import Session, col, select

from app.common.crud import create_entity, delete_entity, get_entity, update_entity
from app.common.query import apply_fuzzy_search
from app.customer.models import Customer, CustomerCreate, CustomerUpdate


def list_customers(
    session: Session,
    query: str | None = None,
) -> list[Customer]:
    stmt = select(Customer).order_by(col(Customer.updated_at).desc())
    stmt = apply_fuzzy_search(
        stmt,
        query,
        [Customer.name, Customer.phone, Customer.address, Customer.notes],
    )
    return list(session.exec(stmt).all())


def get_customer(session: Session, customer_id: int) -> Customer | None:
    return get_entity(session, Customer, customer_id)


def create_customer(session: Session, data: CustomerCreate) -> Customer:
    return create_entity(session, Customer, data)


def update_customer(session: Session, customer_id: int, data: CustomerUpdate) -> Customer | None:
    customer = session.get(Customer, customer_id)
    if not customer:
        return None

    return update_entity(session, customer, data)


def delete_customer(session: Session, customer_id: int) -> bool:
    customer = session.get(Customer, customer_id)
    if not customer:
        return False

    delete_entity(session, customer)
    return True
