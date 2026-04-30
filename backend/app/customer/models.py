from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel


def _validate_required_name(name: str | None) -> str:
    if name is None or not name.strip():
        raise ValueError("客户名称不能为空")
    return name


class CustomerBase(SQLModel):
    name: str
    phone: str = ""
    address: str = ""
    notes: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        return _validate_required_name(name)

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

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None) -> str:
        return _validate_required_name(name)

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
