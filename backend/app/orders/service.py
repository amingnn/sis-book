from datetime import date
from decimal import Decimal

from sqlmodel import Session, select, func

from app.orders.models import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderItem,
)
from app.sales.models import SalesRecord


def _generate_order_number(session: Session, sales_date: date) -> str:
    prefix = f"MC{sales_date.strftime('%Y%m%d')}"
    stmt = (
        select(func.count())
        .select_from(SalesOrder)
        .where(SalesOrder.order_number.startswith(prefix))
    )
    count = session.exec(stmt).one()
    return f"{prefix}{count + 1:03d}"


def _calc_item_subtotal(item: SalesOrderItem) -> Decimal:
    return Decimal(item.total_boxes * item.per_box_qty) * item.unit_price


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

    total = Decimal(0)
    for item_data in data.items:
        item = SalesOrderItem(**item_data.model_dump())
        total += _calc_item_subtotal(item)
        order.items.append(item)

    sales_record = SalesRecord(
        sale_time=data.sales_date,
        customer_name=data.customer_name,
        product=f"销售单{order.order_number}",
        amount=total,
        delivery_time=data.delivery_date,
        payment_method=data.payment_terms,
        cost=Decimal(0),
    )
    session.add(sales_record)
    session.flush()

    order.sales_record_id = sales_record.id
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def delete_order(session: Session, order_id: int) -> bool:
    order = session.get(SalesOrder, order_id)
    if not order:
        return False
    if order.sales_record_id:
        record = session.get(SalesRecord, order.sales_record_id)
        if record:
            session.delete(record)
    session.delete(order)
    session.commit()
    return True
