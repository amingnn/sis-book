from datetime import date, datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from sqlalchemy import case
from sqlmodel import Session, col, func, select

from app.purchases.models import PurchaseOrder
from app.sales import service as sales_service
from app.sales.models import SalesRecord
from app.tasks.models import Task


def _money(value: Decimal | int | float | None) -> float:
    return float(Decimal(str(value or 0)))


def _profit_margin(sales: Decimal, profit: Decimal) -> float:
    if sales == 0:
        return 0.0
    return round(float(profit / sales * 100), 2)


def _month_add(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _month_buckets(today: date, months: int = 6) -> list[dict]:
    first_month = _month_add(today.replace(day=1), -(months - 1))
    return [
        {
            "period": month_start.strftime("%Y-%m"),
            "label": month_start.strftime("%m月"),
            "start": month_start,
            "end": _month_add(month_start, 1),
            "sales": Decimal("0"),
            "cost": Decimal("0"),
            "purchase_amount": Decimal("0"),
            "sales_count": 0,
            "purchase_count": 0,
        }
        for month_start in (_month_add(first_month, index) for index in range(months))
    ]


def _purchase_total_expr():
    return PurchaseOrder.unit_price * PurchaseOrder.box_count * PurchaseOrder.per_box_qty


def _purchase_unpaid_expr():
    remaining_amount = _purchase_total_expr() - PurchaseOrder.paid_amount
    return case((remaining_amount > 0, remaining_amount), else_=0)


def _task_priority_order_expr():
    return case(
        (Task.priority == "high", 0),
        (Task.priority == "medium", 1),
        (Task.priority == "low", 2),
        else_=3,
    )


def _build_month_trend(session: Session, today: date) -> list[dict]:
    buckets = _month_buckets(today)
    bucket_map = {bucket["period"]: bucket for bucket in buckets}
    start_date = buckets[0]["start"]

    sales_period = func.strftime("%Y-%m", col(SalesRecord.sale_time))
    sales_rows = session.exec(
        select(
            sales_period,
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
            func.count(SalesRecord.id),
        )
        .where(col(SalesRecord.sale_time) >= start_date)
        .group_by(sales_period)
    ).all()
    for period, sales, cost, sales_count in sales_rows:
        if period not in bucket_map:
            continue
        bucket = bucket_map[period]
        bucket["sales"] = Decimal(str(sales))
        bucket["cost"] = Decimal(str(cost))
        bucket["sales_count"] = sales_count

    purchase_period = func.strftime("%Y-%m", col(PurchaseOrder.purchase_time))
    purchase_rows = session.exec(
        select(
            purchase_period,
            func.coalesce(func.sum(_purchase_total_expr()), 0),
            func.count(PurchaseOrder.id),
        )
        .where(col(PurchaseOrder.purchase_time) >= start_date)
        .group_by(purchase_period)
    ).all()
    for period, purchase_amount, purchase_count in purchase_rows:
        if period not in bucket_map:
            continue
        bucket = bucket_map[period]
        bucket["purchase_amount"] = Decimal(str(purchase_amount))
        bucket["purchase_count"] = purchase_count

    return [
        {
            "period": bucket["period"],
            "label": bucket["label"],
            "sales": _money(bucket["sales"]),
            "cost": _money(bucket["cost"]),
            "profit": _money(bucket["sales"] - bucket["cost"]),
            "profit_margin": _profit_margin(bucket["sales"], bucket["sales"] - bucket["cost"]),
            "purchase_amount": _money(bucket["purchase_amount"]),
            "sales_count": bucket["sales_count"],
            "purchase_count": bucket["purchase_count"],
        }
        for bucket in buckets
    ]


def _top_products(session: Session, start_date: date, limit: int = 5) -> list[dict]:
    rows = session.exec(
        select(
            SalesRecord.product,
            func.count(SalesRecord.id),
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
        )
        .where(col(SalesRecord.sale_time) >= start_date)
        .group_by(SalesRecord.product)
        .order_by(func.coalesce(func.sum(SalesRecord.amount), 0).desc())
        .limit(limit)
    ).all()

    return [
        {
            "name": product,
            "sales_count": count,
            "sales": _money(sales),
            "profit": _money(Decimal(str(sales)) - Decimal(str(cost))),
            "profit_margin": _profit_margin(Decimal(str(sales)), Decimal(str(sales)) - Decimal(str(cost))),
        }
        for product, count, sales, cost in rows
    ]


def _top_customers(session: Session, start_date: date, limit: int = 5) -> list[dict]:
    rows = session.exec(
        select(
            SalesRecord.customer_name,
            func.count(SalesRecord.id),
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
            func.max(SalesRecord.sale_time),
        )
        .where(col(SalesRecord.sale_time) >= start_date)
        .group_by(SalesRecord.customer_name)
        .order_by(func.coalesce(func.sum(SalesRecord.amount), 0).desc())
        .limit(limit)
    ).all()

    return [
        {
            "name": customer_name,
            "sales_count": count,
            "sales": _money(sales),
            "profit": _money(Decimal(str(sales)) - Decimal(str(cost))),
            "last_sale_time": last_sale_time.isoformat() if isinstance(last_sale_time, date) else str(last_sale_time),
        }
        for customer_name, count, sales, cost, last_sale_time in rows
    ]


def _top_suppliers(session: Session, start_date: date, limit: int = 5) -> list[dict]:
    total_expr = _purchase_total_expr()
    rows = session.exec(
        select(
            PurchaseOrder.supplier_name,
            func.count(PurchaseOrder.id),
            func.coalesce(func.sum(total_expr), 0),
            func.coalesce(func.sum(_purchase_unpaid_expr()), 0),
        )
        .where(col(PurchaseOrder.purchase_time) >= start_date)
        .group_by(PurchaseOrder.supplier_name)
        .order_by(func.coalesce(func.sum(total_expr), 0).desc())
        .limit(limit)
    ).all()

    return [
        {
            "name": supplier_name,
            "purchase_count": purchase_count,
            "amount": _money(amount),
            "unpaid_amount": _money(unpaid_amount),
        }
        for supplier_name, purchase_count, amount, unpaid_amount in rows
    ]


def _task_summary(session: Session, today: date) -> dict:
    open_count = session.exec(
        select(func.count(Task.id)).where(col(Task.status) != "done")
    ).one()
    overdue_count = session.exec(
        select(func.count(Task.id))
        .where(col(Task.status) != "done")
        .where(col(Task.due_date).is_not(None))
        .where(col(Task.due_date) < today)
    ).one()
    due_soon_count = session.exec(
        select(func.count(Task.id))
        .where(col(Task.status) != "done")
        .where(col(Task.due_date).is_not(None))
        .where(col(Task.due_date) >= today)
        .where(col(Task.due_date) <= today + timedelta(days=7))
    ).one()
    recent_open_tasks = session.exec(
        select(Task)
        .where(col(Task.status) != "done")
        .order_by(
            col(Task.due_date).is_(None).asc(),
            col(Task.due_date).asc(),
            _task_priority_order_expr().asc(),
            col(Task.created_at).desc(),
        )
        .limit(5)
    ).all()

    return {
        "open_count": open_count,
        "overdue_count": overdue_count,
        "due_soon_count": due_soon_count,
        "recent_open_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in recent_open_tasks
        ],
    }


def get_dashboard(session: Session) -> dict:
    today = date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    month_sales, month_cost = session.exec(
        select(
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
        ).where(SalesRecord.sale_time >= month_start)
    ).one()

    year_sales, year_cost = session.exec(
        select(
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
        ).where(SalesRecord.sale_time >= year_start)
    ).one()

    unsettled_count, unsettled_amount = session.exec(
        select(
            func.count(SalesRecord.id),
            func.coalesce(func.sum(SalesRecord.amount), 0),
        ).where(SalesRecord.is_settled == False)  # noqa: E712
    ).one()

    recent_sales = session.exec(
        select(SalesRecord).order_by(SalesRecord.sale_time.desc()).limit(5)
    ).all()

    recent_purchases = session.exec(
        select(PurchaseOrder).order_by(PurchaseOrder.purchase_time.desc()).limit(5)
    ).all()
    due_collection = sales_service.get_due_collection_summary(session, today)
    month_sales = Decimal(str(month_sales))
    month_cost = Decimal(str(month_cost))
    year_sales = Decimal(str(year_sales))
    year_cost = Decimal(str(year_cost))
    month_profit = month_sales - month_cost
    year_profit = year_sales - year_cost
    month_trend = _build_month_trend(session, today)
    task_summary = _task_summary(session, today)

    action_items = [
        {
            "type": "collection",
            "title": f"{record['customer_name']} - {record['product']}",
            "amount": record["amount"],
            "date": record["collection_time"],
            "target": "/sales?"
            + urlencode(
                {
                    "due": "collection",
                    "customer_name": record["customer_name"],
                    "product": record["product"],
                }
            ),
        }
        for record in due_collection["due_collection_records"][:3]
    ]
    action_items.extend(
        {
            "type": "task",
            "title": task["title"],
            "amount": None,
            "date": task["due_date"],
            "target": "/tasks?" + urlencode({"keyword": task["title"]}),
        }
        for task in task_summary["recent_open_tasks"][:3]
    )

    return {
        "last_updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "month_sales": float(month_sales),
        "month_cost": float(month_cost),
        "month_profit": float(month_profit),
        "month_profit_margin": _profit_margin(month_sales, month_profit),
        "year_sales": float(year_sales),
        "year_cost": float(year_cost),
        "year_profit": float(year_profit),
        "year_profit_margin": _profit_margin(year_sales, year_profit),
        "unsettled_count": unsettled_count,
        "unsettled_amount": float(Decimal(str(unsettled_amount))),
        "due_collection_count": due_collection["due_collection_count"],
        "due_collection_amount": due_collection["due_collection_amount"],
        "due_collection_records": due_collection["due_collection_records"],
        "month_trend": month_trend,
        "top_products": _top_products(session, year_start),
        "top_customers": _top_customers(session, year_start),
        "top_suppliers": _top_suppliers(session, year_start),
        "task_summary": task_summary,
        "action_items": action_items[:6],
        "recent_sales": [
            {
                "id": record.id,
                "sale_time": record.sale_time.isoformat(),
                "customer_name": record.customer_name,
                "product": record.product,
                "amount": float(record.amount),
                "gross_profit": float(record.amount - record.cost),
                "is_settled": record.is_settled,
            }
            for record in recent_sales
        ],
        "recent_purchases": [
            {
                "id": record.id,
                "purchase_time": record.purchase_time.isoformat(),
                "supplier_name": record.supplier_name,
                "product_name": record.product_name,
                "total_amount": float(record.unit_price * record.box_count * record.per_box_qty),
                "unpaid_amount": float(
                    max(Decimal("0"), record.unit_price * record.box_count * record.per_box_qty - record.paid_amount)
                ),
            }
            for record in recent_purchases
        ],
    }
