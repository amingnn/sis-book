from sqlmodel import Session, col, select

from app.common.crud import create_entity, delete_entity, get_entity, update_entity
from app.common.query import apply_fuzzy_search
from app.supplier.models import Supplier, SupplierCreate, SupplierUpdate


def list_suppliers(session: Session, query: str | None = None) -> list[Supplier]:
    stmt = select(Supplier).order_by(col(Supplier.updated_at).desc())
    stmt = apply_fuzzy_search(
        stmt,
        query,
        [Supplier.name, Supplier.phone, Supplier.address, Supplier.notes],
    )
    return list(session.exec(stmt).all())


def get_supplier(session: Session, supplier_id: int) -> Supplier | None:
    return get_entity(session, Supplier, supplier_id)


def create_supplier(session: Session, data: SupplierCreate) -> Supplier:
    return create_entity(session, Supplier, data)


def update_supplier(session: Session, supplier_id: int, data: SupplierUpdate) -> Supplier | None:
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        return None

    return update_entity(session, supplier, data)


def delete_supplier(session: Session, supplier_id: int) -> bool:
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        return False

    delete_entity(session, supplier)
    return True
