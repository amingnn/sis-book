from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.orders.models import SalesOrderCreate, SalesOrderResponse, SalesOrderUpdate
from app.orders.service import (
    create_order,
    delete_order,
    get_order,
    list_orders,
    update_order,
)

router = APIRouter(prefix="/api/orders", tags=["开单"])


@router.get("", response_model=list[SalesOrderResponse])
def api_list_orders(
    q: str | None = Query(None),
    order_number: str | None = Query(None),
    customer_name: str | None = Query(None),
    payment_terms: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: Session = Depends(get_session),
):
    return list_orders(
        session,
        q=q,
        order_number=order_number,
        customer_name=customer_name,
        payment_terms=payment_terms,
        start_date=start_date,
        end_date=end_date,
    )


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


@router.put("/{order_id}", response_model=SalesOrderResponse)
def api_update_order(
    order_id: int,
    data: SalesOrderUpdate,
    session: Session = Depends(get_session),
):
    if order := update_order(session, order_id, data):
        return order
    raise HTTPException(status_code=404, detail="销售单不存在")


@router.delete("/{order_id}", status_code=204)
def api_delete_order(order_id: int, session: Session = Depends(get_session)):
    if not delete_order(session, order_id):
        raise HTTPException(status_code=404, detail="销售单不存在")
