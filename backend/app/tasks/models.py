from datetime import date, datetime

from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    title: str
    description: str = ""
    category: str = "其他"
    priority: str = "medium"
    status: str = "todo"
    due_date: date | None = None
    related_type: str = ""
    related_id: int | None = None
    notes: str = ""


class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None
    related_type: str | None = None
    related_id: int | None = None
    notes: str | None = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    completed_at: datetime | None


class TaskQuickUpdate(SQLModel):
    status: str

