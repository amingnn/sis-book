from typing import Literal

from pydantic import BaseModel


class DueCollectionRecord(BaseModel):
    id: int
    customer_name: str
    product: str
    amount: float
    collection_time: str | None


class MonthTrendPoint(BaseModel):
    period: str
    label: str
    sales: float
    cost: float
    profit: float
    profit_margin: float
    purchase_amount: float
    sales_count: int
    purchase_count: int


class TopProduct(BaseModel):
    name: str
    sales_count: int
    sales: float
    profit: float
    profit_margin: float


class TopCustomer(BaseModel):
    name: str
    sales_count: int
    sales: float
    profit: float
    last_sale_time: str


class TopSupplier(BaseModel):
    name: str
    purchase_count: int
    amount: float
    unpaid_amount: float


class RecentOpenTask(BaseModel):
    id: int
    title: str
    priority: str
    status: str
    due_date: str | None


class TaskSummary(BaseModel):
    open_count: int
    overdue_count: int
    due_soon_count: int
    recent_open_tasks: list[RecentOpenTask]


class ActionItem(BaseModel):
    type: Literal["collection", "task"]
    title: str
    amount: float | None
    date: str | None
    target: str


class RecentSale(BaseModel):
    id: int
    sale_time: str
    customer_name: str
    product: str
    amount: float
    gross_profit: float
    is_settled: bool


class RecentPurchase(BaseModel):
    id: int
    purchase_time: str
    supplier_name: str
    product_name: str
    total_amount: float
    unpaid_amount: float


class DashboardResponse(BaseModel):
    last_updated_at: str
    month_sales: float
    month_cost: float
    month_profit: float
    month_profit_margin: float
    year_sales: float
    year_cost: float
    year_profit: float
    year_profit_margin: float
    unsettled_count: int
    unsettled_amount: float
    due_collection_count: int
    due_collection_amount: float
    due_collection_records: list[DueCollectionRecord]
    month_trend: list[MonthTrendPoint]
    top_products: list[TopProduct]
    top_customers: list[TopCustomer]
    top_suppliers: list[TopSupplier]
    task_summary: TaskSummary
    action_items: list[ActionItem]
    recent_sales: list[RecentSale]
    recent_purchases: list[RecentPurchase]
