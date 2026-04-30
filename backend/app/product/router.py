from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.product import service
from app.product.models import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["产品"])


@router.get("", response_model=list[ProductResponse])
def read_products(
    q: str | None = Query(None),
    session: Session = Depends(get_session),
):
    return service.list_products(session, query=q)


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, session: Session = Depends(get_session)):
    if product := service.get_product(session, product_id):
        return product
    raise HTTPException(status_code=404, detail="产品不存在")


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, session: Session = Depends(get_session)):
    return service.create_product(session, data)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session),
):
    if product := service.update_product(session, product_id, data):
        return product
    raise HTTPException(status_code=404, detail="产品不存在")


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    if not service.delete_product(session, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")
