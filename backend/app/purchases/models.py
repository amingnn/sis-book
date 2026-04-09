from datetime import date, datetime
from decimal import Decimal

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class PurchaseOrderBase(SQLModel):
    purchase_time: date
    supplier_name: str
    product_name: str
    box_count: int
    per_box_qty: int
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    notes: str = ""


class PurchaseOrder(PurchaseOrderBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderUpdate(SQLModel):
    purchase_time: date | None = None
    supplier_name: str | None = None
    product_name: str | None = None
    box_count: int | None = None
    per_box_qty: int | None = None
    unit_price: Decimal | None = None
    notes: str | None = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    created_at: datetime

    @computed_field
    @property
    def total_qty(self) -> int:
        return self.box_count * self.per_box_qty

    @computed_field
    @property
    def total_amount(self) -> Decimal:
        return self.unit_price * self.box_count * self.per_box_qty
