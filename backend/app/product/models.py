from datetime import datetime
from decimal import Decimal

from pydantic import field_validator
from sqlmodel import Field, SQLModel


def _validate_required_name(name: str | None) -> str:
    if name is None or not name.strip():
        raise ValueError("产品名称不能为空")
    return name


class ProductBase(SQLModel):
    name: str
    image: str = ""
    per_box_qty: int = 0
    box_spec: str = ""
    volume: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=3)
    purchase_price: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    stock_qty: int = 0
    notes: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        return _validate_required_name(name)


class Product(ProductBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    name: str | None = None
    image: str | None = None
    per_box_qty: int | None = None
    box_spec: str | None = None
    volume: Decimal | None = None
    purchase_price: Decimal | None = None
    stock_qty: int | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None) -> str:
        return _validate_required_name(name)


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
