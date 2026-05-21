from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, func, or_, select

from app.orders.images import store_order_item_image
from app.orders.models import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderItem,
    SalesOrderItemCreate,
    SalesOrderUpdate,
)
from app.product.models import Product
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


def list_orders(
    session: Session,
    q: str | None = None,
    order_number: str | None = None,
    customer_name: str | None = None,
    payment_terms: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SalesOrder]:
    stmt = select(SalesOrder)
    if q:
        stmt = stmt.join(SalesOrderItem, isouter=True).where(
            or_(
                col(SalesOrder.order_number).contains(q),
                col(SalesOrder.customer_name).contains(q),
                col(SalesOrder.customer_phone).contains(q),
                col(SalesOrder.delivery_address).contains(q),
                col(SalesOrder.notes).contains(q),
                col(SalesOrderItem.product_name).contains(q),
                col(SalesOrderItem.color_spec).contains(q),
                col(SalesOrderItem.notes).contains(q),
            )
        ).distinct()
    if order_number:
        stmt = stmt.where(col(SalesOrder.order_number).contains(order_number))
    if customer_name:
        stmt = stmt.where(col(SalesOrder.customer_name).contains(customer_name))
    if payment_terms:
        stmt = stmt.where(col(SalesOrder.payment_terms).contains(payment_terms))
    if start_date:
        stmt = stmt.where(col(SalesOrder.sales_date) >= start_date)
    if end_date:
        stmt = stmt.where(col(SalesOrder.sales_date) <= end_date)
    stmt = stmt.order_by(SalesOrder.id.desc())
    orders = list(session.exec(stmt).all())
    _hydrate_missing_item_images(session, orders)
    return orders


def get_order(session: Session, order_id: int) -> SalesOrder | None:
    order = session.get(SalesOrder, order_id)
    if order:
        _hydrate_missing_item_images(session, [order])
    return order


def _calc_order_total(items: list[SalesOrderItem]) -> Decimal:
    return sum(
        (
            Decimal(item.total_boxes)
            * Decimal(item.per_box_qty)
            * Decimal(str(item.unit_price))
        )
        for item in items
    )


def _build_order_product_summary(items: list[SalesOrderItem]) -> str:
    names = [item.product_name.strip() for item in items if item.product_name.strip()]
    if not names:
        return "销售单商品"
    if len(names) == 1:
        return names[0]
    return f"{names[0]} 等{len(names)}项"


def _build_order_sales_notes(order: SalesOrder) -> str:
    parts = [f"开单单号：{order.order_number}"]
    if order.notes.strip():
        parts.append(order.notes.strip())
    return "\n".join(parts)


def _hydrate_missing_item_images(session: Session, orders: list[SalesOrder]) -> None:
    product_names = {
        item.product_name.strip()
        for order in orders
        for item in order.items
        if not item.image and item.product_name.strip()
    }
    if not product_names:
        return

    products = session.exec(
        select(Product).where(col(Product.name).in_(product_names))
    ).all()
    image_lookup = {product.name: product.image for product in products if product.image}
    if not image_lookup:
        return

    for order in orders:
        for item in order.items:
            if not item.image:
                item.image = image_lookup.get(item.product_name.strip(), "")


def _build_order_item(item_data: SalesOrderItemCreate, order_number: str) -> SalesOrderItem:
    item_payload = item_data.model_dump()
    item_payload["image"] = store_order_item_image(
        item_payload.get("image", ""),
        order_number,
        item_payload.get("product_name", ""),
    )
    return SalesOrderItem(**item_payload)


def _sync_sales_record_for_order(session: Session, order: SalesOrder) -> None:
    total_amount = _calc_order_total(order.items)
    product_summary = _build_order_product_summary(order.items)

    if order.sales_record_id:
        record = session.get(SalesRecord, order.sales_record_id)
    else:
        record = None

    if not record:
        record = SalesRecord()

    record.sale_time = order.sales_date
    record.customer_name = order.customer_name
    record.product = product_summary
    record.amount = total_amount
    record.delivery_time = order.delivery_date
    record.collection_time = None
    record.is_settled = False
    record.payment_method = order.payment_terms
    # 开单流程没有成本字段，先以金额兜底避免自动生成错误利润，后续可在销售记录中补充。
    record.cost = total_amount
    record.notes = _build_order_sales_notes(order)

    session.add(record)
    session.flush()
    order.sales_record_id = record.id


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
        order.items.append(_build_order_item(item_data, order.order_number))

    session.add(order)
    session.flush()
    _hydrate_missing_item_images(session, [order])
    _sync_sales_record_for_order(session, order)
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
        order.items.append(_build_order_item(item_data, order.order_number))

    session.add(order)
    session.flush()
    _hydrate_missing_item_images(session, [order])
    _sync_sales_record_for_order(session, order)
    session.commit()
    session.refresh(order)
    return order


def delete_order(session: Session, order_id: int) -> bool:
    order = session.get(SalesOrder, order_id)
    if not order:
        return False
    if order.sales_record_id and (record := session.get(SalesRecord, order.sales_record_id)):
        session.delete(record)
    session.delete(order)
    session.commit()
    return True
