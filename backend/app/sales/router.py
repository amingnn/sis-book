from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.sales import service
from app.sales.models import SalesRecordCreate, SalesRecordResponse, SalesRecordUpdate

router = APIRouter(prefix="/api/sales", tags=["销售记录"])


@router.get("/summary")
def read_summary(
    q: str | None = Query(None),
    customer_name: str | None = Query(None),
    product: str | None = Query(None),
    is_settled: bool | None = Query(None),
    payment_method: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    due_collection: bool = Query(False),
    session: Session = Depends(get_session),
):
    return service.get_summary(
        session,
        q,
        customer_name,
        product,
        is_settled,
        payment_method,
        start_date,
        end_date,
        due_collection,
    )


@router.get("", response_model=list[SalesRecordResponse])
def read_records(
    q: str | None = Query(None),
    customer_name: str | None = Query(None),
    product: str | None = Query(None),
    is_settled: bool | None = Query(None),
    payment_method: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    due_collection: bool = Query(False),
    session: Session = Depends(get_session),
):
    return service.list_records(
        session,
        q,
        customer_name,
        product,
        is_settled,
        payment_method,
        start_date,
        end_date,
        due_collection,
    )


@router.get("/{record_id}", response_model=SalesRecordResponse)
def read_record(record_id: int, session: Session = Depends(get_session)):
    if record := service.get_record(session, record_id):
        return record
    else:
        raise HTTPException(status_code=404, detail="记录不存在")


@router.post("", response_model=SalesRecordResponse, status_code=201)
def create_record(data: SalesRecordCreate, session: Session = Depends(get_session)):
    return service.create_record(session, data)


@router.put("/{record_id}", response_model=SalesRecordResponse)
def update_record(record_id: int, data: SalesRecordUpdate, session: Session = Depends(get_session)):
    if record := service.update_record(session, record_id, data):
        return record
    else:
        raise HTTPException(status_code=404, detail="记录不存在")


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, session: Session = Depends(get_session)):
    if not service.delete_record(session, record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
