from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel


class SalesOrderItemBase(SQLModel):
    product_name: str
    color_spec: str = ""
    total_boxes: int
    per_box_qty: int
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    box_size: str = ""
    notes: str = ""
    image: str = ""


class SalesOrderItem(SalesOrderItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sales_order_id: int = Field(foreign_key="salesorder.id")
    sales_order: "SalesOrder" = Relationship(back_populates="items")


class SalesOrderBase(SQLModel):
    order_number: str = ""
    customer_name: str
    customer_phone: str = ""
    delivery_address: str = ""
    sales_date: date
    delivery_date: date | None = None
    payment_terms: str = ""
    notes: str = ""


class SalesOrder(SalesOrderBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sales_record_id: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    items: list[SalesOrderItem] = Relationship(
        back_populates="sales_order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderCreate(SalesOrderBase):
    items: list[SalesOrderItemCreate]


class SalesOrderUpdate(SalesOrderBase):
    items: list[SalesOrderItemCreate]


class SalesOrderItemResponse(SalesOrderItemBase):
    id: int
    sales_order_id: int


class SalesOrderResponse(SalesOrderBase):
    id: int
    sales_record_id: int | None
    created_at: datetime
    items: list[SalesOrderItemResponse]
