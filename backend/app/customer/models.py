from datetime import datetime

from sqlmodel import Field, SQLModel


class CustomerBase(SQLModel):
    name: str
    phone: str = ""
    address: str = ""
    notes: str = ""

class Customer(CustomerBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(SQLModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

