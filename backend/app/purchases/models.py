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
    paid_amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
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
    paid_amount: Decimal | None = None
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

    @computed_field
    @property
    def unpaid_amount(self) -> Decimal:
        total_amount = self.total_amount
        if self.paid_amount >= total_amount:
            return Decimal("0")
        return total_amount - self.paid_amount


    @computed_field
    @property
    def is_settled(self) -> bool:
        return self.unpaid_amount <= Decimal("0")


class PurchaseOrderPage(SQLModel):
    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
