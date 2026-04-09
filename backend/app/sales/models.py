from datetime import date, datetime
from decimal import Decimal

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class SalesRecordBase(SQLModel):
    sale_time: date
    customer_name: str
    product: str
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    delivery_time: date | None = None
    is_settled: bool = False
    payment_method: str = ""
    cost: Decimal = Field(max_digits=12, decimal_places=2)
    notes: str = ""


class SalesRecord(SalesRecordBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class SalesRecordCreate(SalesRecordBase):
    pass


class SalesRecordUpdate(SQLModel):
    sale_time: date | None = None
    customer_name: str | None = None
    product: str | None = None
    amount: Decimal | None = None
    delivery_time: date | None = None
    is_settled: bool | None = None
    payment_method: str | None = None
    cost: Decimal | None = None
    notes: str | None = None


class SalesRecordResponse(SalesRecordBase):
    id: int
    created_at: datetime

    @computed_field
    @property
    def gross_profit(self) -> Decimal:
        return self.amount - self.cost

    @computed_field
    @property
    def profit_margin(self) -> float:
        if self.cost == 0:
            return 0.0
        return float((self.amount - self.cost) / self.cost * 100)
