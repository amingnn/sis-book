from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, func, select

from .models import (
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderPage,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)


def _clamp_paid_amount(data: PurchaseOrderCreate | PurchaseOrderUpdate) -> dict:
    payload = data.model_dump(exclude_unset=True)
    box_count = payload.get("box_count")
    per_box_qty = payload.get("per_box_qty")
    unit_price = payload.get("unit_price")
    paid_amount = payload.get("paid_amount")
    if (
        paid_amount is None
        or box_count is None
        or per_box_qty is None
        or unit_price is None
    ):
        return payload
    total_amount = Decimal(str(unit_price)) * box_count * per_box_qty
    payload["paid_amount"] = min(Decimal(str(paid_amount)), total_amount)
    return payload


def list_purchases(
    session: Session,
    *,
    supplier_name: str | None = None,
    product_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder)
    if supplier_name:
        stmt = stmt.where(PurchaseOrder.supplier_name.contains(supplier_name))
    if product_name:
        stmt = stmt.where(PurchaseOrder.product_name.contains(product_name))
    if start_date:
        stmt = stmt.where(PurchaseOrder.purchase_time >= start_date)
    if end_date:
        stmt = stmt.where(PurchaseOrder.purchase_time <= end_date)
    stmt = stmt.order_by(PurchaseOrder.purchase_time.desc())
    return list(session.exec(stmt).all())


def get_supplier_purchase_page(
    session: Session,
    *,
    supplier_name: str,
    page: int = 1,
    page_size: int = 10,
) -> PurchaseOrderPage:
    base_stmt = select(PurchaseOrder).where(PurchaseOrder.supplier_name == supplier_name)
    total = session.exec(
        select(func.count()).select_from(base_stmt.order_by(None).subquery())
    ).one()
    stmt = (
        base_stmt.order_by(col(PurchaseOrder.purchase_time).desc(), col(PurchaseOrder.id).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(session.exec(stmt).all())
    return PurchaseOrderPage(
        items=[PurchaseOrderResponse.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_purchase(session: Session, purchase_id: int) -> PurchaseOrder | None:
    return session.get(PurchaseOrder, purchase_id)


def create_purchase(session: Session, data: PurchaseOrderCreate) -> PurchaseOrder:
    order = PurchaseOrder.model_validate(_clamp_paid_amount(data))
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def update_purchase(
    session: Session, order: PurchaseOrder, data: PurchaseOrderUpdate
) -> PurchaseOrder:
    update_data = _clamp_paid_amount(data)
    order.sqlmodel_update(update_data)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def delete_purchase(session: Session, order: PurchaseOrder) -> None:
    session.delete(order)
    session.commit()
