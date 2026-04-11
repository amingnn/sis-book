from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.orders.models import SalesOrderCreate, SalesOrderResponse
from app.orders.service import create_order, delete_order, get_order, list_orders

router = APIRouter(prefix="/api/orders", tags=["开单"])


@router.get("", response_model=list[SalesOrderResponse])
def api_list_orders(session: Session = Depends(get_session)):
    return list_orders(session)


@router.get("/{order_id}", response_model=SalesOrderResponse)
def api_get_order(order_id: int, session: Session = Depends(get_session)):
    if order := get_order(session, order_id):
        return order
    else:
        raise HTTPException(status_code=404, detail="销售单不存在")


@router.post("", response_model=SalesOrderResponse, status_code=201)
def api_create_order(
    data: SalesOrderCreate,
    session: Session = Depends(get_session),
):
    return create_order(session, data)


@router.delete("/{order_id}", status_code=204)
def api_delete_order(order_id: int, session: Session = Depends(get_session)):
    if not delete_order(session, order_id):
        raise HTTPException(status_code=404, detail="销售单不存在")
