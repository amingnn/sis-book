from datetime import date

from sqlmodel import Session, select

from .models import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate


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


def get_purchase(session: Session, purchase_id: int) -> PurchaseOrder | None:
    return session.get(PurchaseOrder, purchase_id)


def create_purchase(session: Session, data: PurchaseOrderCreate) -> PurchaseOrder:
    order = PurchaseOrder.model_validate(data)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def update_purchase(
    session: Session, order: PurchaseOrder, data: PurchaseOrderUpdate
) -> PurchaseOrder:
    update_data = data.model_dump(exclude_unset=True)
    order.sqlmodel_update(update_data)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def delete_purchase(session: Session, order: PurchaseOrder) -> None:
    session.delete(order)
    session.commit()
