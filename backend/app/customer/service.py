from datetime import datetime

from sqlmodel import Session, col, or_, select

from app.customer.models import Customer, CustomerCreate, CustomerUpdate

def _apply_filters(
    statement,
    *,
    query: str | None,
):
    if query:
        statement = statement.where(
            or_(
                col(Customer.name).contains(query), 
                col(Customer.phone).contains(query), 
                col(Customer.address).contains(query), 
                col(Customer.notes).contains(query)
            )
        )
    return statement

def list_customers(
    session: Session,
    query: str | None = None,
) -> list[Customer]:
    stmt = select(Customer).order_by(col(Customer.updated_at).desc())
    stmt = _apply_filters(
        stmt,
        query=query,
    )
    return list(session.exec(stmt).all())


def get_customer(session: Session, customer_id: int) -> Customer | None:
    return session.get(Customer, customer_id)


def create_customer(session: Session, data: CustomerCreate) -> Customer:
    customer = Customer.model_validate(data)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def update_customer(session: Session, customer_id: int, data: CustomerUpdate) -> Customer | None:
    customer = session.get(Customer, customer_id)
    if not customer:
        return None
    
    customer.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    customer.updated_at = datetime.now()
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def delete_customer(session: Session, customer_id: int) -> bool:
    customer = session.get(Customer, customer_id)
    if not customer:
        return False
    
    session.delete(customer)
    session.commit()
    return True

