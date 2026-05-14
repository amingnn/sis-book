from datetime import date
from decimal import Decimal

from sqlmodel import Session, func, select

from app.purchases.models import PurchaseOrder
from app.sales import service as sales_service
from app.sales.models import SalesRecord


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

    return {
        "month_sales": float(month_sales),
        "month_cost": float(month_cost),
        "month_profit": float(month_sales - month_cost),
        "year_sales": float(year_sales),
        "year_cost": float(year_cost),
        "year_profit": float(year_sales - year_cost),
        "unsettled_count": unsettled_count,
        "unsettled_amount": float(Decimal(str(unsettled_amount))),
        "due_collection_count": due_collection["due_collection_count"],
        "due_collection_amount": due_collection["due_collection_amount"],
        "due_collection_records": due_collection["due_collection_records"],
        "recent_sales": [
            {
                "id": record.id,
                "sale_time": record.sale_time.isoformat(),
                "customer_name": record.customer_name,
                "product": record.product,
                "amount": float(record.amount),
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
            }
            for record in recent_purchases
        ],
    }
