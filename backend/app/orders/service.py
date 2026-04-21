from datetime import date

from sqlmodel import Session, col, func, select

from app.orders.models import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderItem,
    SalesOrderUpdate,
)


def _generate_order_number(session: Session, sales_date: date) -> str:
    prefix = f"MC{sales_date.strftime('%Y%m%d')}"
    stmt = (
        select(func.count())
        .select_from(SalesOrder)
        .where(SalesOrder.order_number.startswith(prefix))
    )
    count = session.exec(stmt).one()
    return f"{prefix}{count + 1:03d}"


def list_orders(
    session: Session,
    order_number: str | None = None,
    customer_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SalesOrder]:
    stmt = select(SalesOrder)
    if order_number:
        stmt = stmt.where(col(SalesOrder.order_number).contains(order_number))
    if customer_name:
        stmt = stmt.where(col(SalesOrder.customer_name).contains(customer_name))
    if start_date:
        stmt = stmt.where(col(SalesOrder.sales_date) >= start_date)
    if end_date:
        stmt = stmt.where(col(SalesOrder.sales_date) <= end_date)
    stmt = stmt.order_by(SalesOrder.id.desc())
    return list(session.exec(stmt).all())


def get_order(session: Session, order_id: int) -> SalesOrder | None:
    return session.get(SalesOrder, order_id)


def create_order(session: Session, data: SalesOrderCreate) -> SalesOrder:
    order = SalesOrder(
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        delivery_address=data.delivery_address,
        sales_date=data.sales_date,
        delivery_date=data.delivery_date,
        payment_terms=data.payment_terms,
        notes=data.notes,
    )
    order.order_number = _generate_order_number(session, data.sales_date)

    for item_data in data.items:
        item = SalesOrderItem(**item_data.model_dump())
        order.items.append(item)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def update_order(
    session: Session,
    order_id: int,
    data: SalesOrderUpdate,
) -> SalesOrder | None:
    order = session.get(SalesOrder, order_id)
    if not order:
        return None

    order.customer_name = data.customer_name
    order.customer_phone = data.customer_phone
    order.delivery_address = data.delivery_address
    order.sales_date = data.sales_date
    order.delivery_date = data.delivery_date
    order.payment_terms = data.payment_terms
    order.notes = data.notes

    order.items.clear()
    for item_data in data.items:
        order.items.append(SalesOrderItem(**item_data.model_dump()))

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def delete_order(session: Session, order_id: int) -> bool:
    order = session.get(SalesOrder, order_id)
    if not order:
        return False
    session.delete(order)
    session.commit()
    return True
