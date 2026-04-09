from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session

from .models import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from . import service

router = APIRouter(prefix="/api/purchases", tags=["采购单"])


@router.get("", response_model=list[PurchaseOrderResponse])
def list_purchases(
    supplier_name: str | None = Query(None),
    product_name: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.list_purchases(
        session,
        supplier_name=supplier_name,
        product_name=product_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{purchase_id}", response_model=PurchaseOrderResponse)
def get_purchase(purchase_id: int, session: Session = Depends(get_session)):
    order = service.get_purchase(session, purchase_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return order


@router.post("", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase(
    data: PurchaseOrderCreate, session: Session = Depends(get_session)
):
    return service.create_purchase(session, data)


@router.put("/{purchase_id}", response_model=PurchaseOrderResponse)
def update_purchase(
    purchase_id: int,
    data: PurchaseOrderUpdate,
    session: Session = Depends(get_session),
):
    order = service.get_purchase(session, purchase_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return service.update_purchase(session, order, data)


@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(purchase_id: int, session: Session = Depends(get_session)):
    order = service.get_purchase(session, purchase_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购单不存在")
    service.delete_purchase(session, order)
