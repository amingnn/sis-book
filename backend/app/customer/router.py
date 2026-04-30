from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from app.customer.models import CustomerCreate, CustomerResponse, CustomerUpdate
from app.database import get_session
from app.customer import service

router = APIRouter(prefix="/api/customers", tags=["客户"])

@router.get("", response_model=list[CustomerResponse])
def read_customers(
    q: str | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.list_customers(
        session,
        query=q,
    )
    

@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(customer_id: int, session: Session = Depends(get_session)):
    if customer := service.get_customer(session, customer_id):
        return customer
    else:
        raise HTTPException(status_code=404, detail="客户不存在")


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, session: Session = Depends(get_session)):
    return service.create_customer(session, data=data)



@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate, session: Session = Depends(get_session)):
    if customer := service.update_customer(session, customer_id=customer_id, data=data):
        return customer
    else:
        raise HTTPException(status_code=404, detail="客户不存在")
    

@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, session: Session = Depends(get_session)):
    if not service.delete_customer(session, customer_id=customer_id):
        raise HTTPException(status_code=404, detail="客户不存在")
