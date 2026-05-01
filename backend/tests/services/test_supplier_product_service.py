from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.product import service as product_service
from app.product.models import ProductCreate, ProductUpdate
from app.supplier import service as supplier_service
from app.supplier.models import SupplierCreate, SupplierUpdate


def test_supplier_crud_and_search(session):
    supplier = supplier_service.create_supplier(
        session,
        SupplierCreate(
            name="胜利厂家",
            phone="13800000000",
            address="义乌",
            notes="羽毛球",
        ),
    )

    assert supplier.id is not None
    assert supplier_service.list_suppliers(session, query="羽毛球")[0].name == "胜利厂家"

    updated = supplier_service.update_supplier(
        session,
        supplier.id,
        SupplierUpdate(address="广州"),
    )

    assert updated is not None
    assert updated.address == "广州"
    assert supplier_service.delete_supplier(session, supplier.id) is True
    assert supplier_service.get_supplier(session, supplier.id) is None


def test_supplier_rejects_empty_name():
    with pytest.raises(ValidationError):
        SupplierCreate(name=" ")

    with pytest.raises(ValidationError):
        SupplierUpdate(name=None)


def test_product_crud_and_search(session):
    product = product_service.create_product(
        session,
        ProductCreate(
            name="羽毛球",
            image="img/product.png",
            per_box_qty=12,
            box_spec="60*40*30",
            volume=Decimal("0.072"),
            purchase_price=Decimal("2.50"),
            stock_qty=120,
        ),
    )

    assert product.id is not None
    assert product_service.list_products(session, query="60*40")[0].name == "羽毛球"

    updated = product_service.update_product(
        session,
        product.id,
        ProductUpdate(stock_qty=100, notes="热销"),
    )

    assert updated is not None
    assert updated.stock_qty == 100
    assert updated.notes == "热销"
    assert product_service.delete_product(session, product.id) is True
    assert product_service.get_product(session, product.id) is None


def test_product_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProductCreate(name="")

    with pytest.raises(ValidationError):
        ProductUpdate(name=None)
