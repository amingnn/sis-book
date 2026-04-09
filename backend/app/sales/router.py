from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.sales import service
from app.sales.models import SalesRecordCreate, SalesRecordResponse, SalesRecordUpdate

router = APIRouter(prefix="/api/sales", tags=["销售记录"])


@router.get("/summary")
def read_summary(
    customer_name: str | None = Query(None),
    is_settled: bool | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.get_summary(session, customer_name, is_settled, start_date, end_date)


@router.get("", response_model=list[SalesRecordResponse])
def read_records(
    customer_name: str | None = Query(None),
    is_settled: bool | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.list_records(session, customer_name, is_settled, start_date, end_date)


@router.get("/{record_id}", response_model=SalesRecordResponse)
def read_record(record_id: int, session: Session = Depends(get_session)):
    record = service.get_record(session, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("", response_model=SalesRecordResponse, status_code=201)
def create_record(data: SalesRecordCreate, session: Session = Depends(get_session)):
    return service.create_record(session, data)


@router.put("/{record_id}", response_model=SalesRecordResponse)
def update_record(record_id: int, data: SalesRecordUpdate, session: Session = Depends(get_session)):
    record = service.update_record(session, record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, session: Session = Depends(get_session)):
    if not service.delete_record(session, record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
