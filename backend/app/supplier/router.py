from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.common.errors import raise_not_found
from app.database import get_session
from app.supplier import service
from app.supplier.models import SupplierCreate, SupplierResponse, SupplierUpdate

router = APIRouter(prefix="/api/suppliers", tags=["厂家"])


@router.get("", response_model=list[SupplierResponse])
def read_suppliers(
    q: str | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.list_suppliers(session, query=q)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def read_supplier(supplier_id: int, session: Session = Depends(get_session)):
    if supplier := service.get_supplier(session, supplier_id):
        return supplier
    raise_not_found("厂家不存在")


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(data: SupplierCreate, session: Session = Depends(get_session)):
    return service.create_supplier(session, data)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    session: Session = Depends(get_session),
):
    if supplier := service.update_supplier(session, supplier_id, data):
        return supplier
    raise_not_found("厂家不存在")


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int, session: Session = Depends(get_session)):
    if not service.delete_supplier(session, supplier_id):
        raise_not_found("厂家不存在")
