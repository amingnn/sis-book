from datetime import datetime

from sqlmodel import Session, col, or_, select

from app.supplier.models import Supplier, SupplierCreate, SupplierUpdate


def list_suppliers(session: Session, query: str | None = None) -> list[Supplier]:
    stmt = select(Supplier).order_by(col(Supplier.updated_at).desc())
    if query:
        stmt = stmt.where(
            or_(
                col(Supplier.name).contains(query),
                col(Supplier.phone).contains(query),
                col(Supplier.address).contains(query),
                col(Supplier.notes).contains(query),
            )
        )
    return list(session.exec(stmt).all())


def get_supplier(session: Session, supplier_id: int) -> Supplier | None:
    return session.get(Supplier, supplier_id)


def create_supplier(session: Session, data: SupplierCreate) -> Supplier:
    supplier = Supplier.model_validate(data)
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


def update_supplier(session: Session, supplier_id: int, data: SupplierUpdate) -> Supplier | None:
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        return None

    supplier.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    supplier.updated_at = datetime.now()
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


def delete_supplier(session: Session, supplier_id: int) -> bool:
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        return False

    session.delete(supplier)
    session.commit()
    return True
