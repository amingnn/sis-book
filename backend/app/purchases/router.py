from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session

from .models import (
    PurchaseOrderCreate,
    PurchaseOrderPage,
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


@router.get("/supplier-history", response_model=PurchaseOrderPage)
def get_supplier_purchase_page(
    supplier_name: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
):
    return service.get_supplier_purchase_page(
        session, supplier_name=supplier_name, page=page, page_size=page_size
    )


@router.get("/{purchase_id}", response_model=PurchaseOrderResponse)
def get_purchase(purchase_id: int, session: Session = Depends(get_session)):
    if order := service.get_purchase(session, purchase_id):
        return order
    else:
        raise HTTPException(status_code=404, detail="采购单不存在")


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
    if order := service.get_purchase(session, purchase_id):
        return service.update_purchase(session, order, data)
    else:
        raise HTTPException(status_code=404, detail="采购单不存在")


@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(purchase_id: int, session: Session = Depends(get_session)):
    if order := service.get_purchase(session, purchase_id):
        service.delete_purchase(session, order)
    else:
        raise HTTPException(status_code=404, detail="采购单不存在")
