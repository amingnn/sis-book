from datetime import date

from sqlmodel import Session, select, func

from app.orders.models import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderItem,
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


def list_orders(session: Session) -> list[SalesOrder]:
    stmt = select(SalesOrder).order_by(SalesOrder.id.desc())
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


def delete_order(session: Session, order_id: int) -> bool:
    order = session.get(SalesOrder, order_id)
    if not order:
        return False
    session.delete(order)
    session.commit()
    return True
