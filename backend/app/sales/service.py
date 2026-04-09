from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, func, select

from app.sales.models import SalesRecord, SalesRecordCreate, SalesRecordUpdate


def _apply_filters(statement, *, customer_name: str | None, is_settled: bool | None, start_date: date | None, end_date: date | None):
    if customer_name:
        statement = statement.where(col(SalesRecord.customer_name).contains(customer_name))
    if is_settled is not None:
        statement = statement.where(col(SalesRecord.is_settled) == is_settled)
    if start_date:
        statement = statement.where(col(SalesRecord.sale_time) >= start_date)
    if end_date:
        statement = statement.where(col(SalesRecord.sale_time) <= end_date)
    return statement


def list_records(
    session: Session,
    customer_name: str | None = None,
    is_settled: bool | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SalesRecord]:
    stmt = select(SalesRecord).order_by(col(SalesRecord.sale_time).desc())
    stmt = _apply_filters(stmt, customer_name=customer_name, is_settled=is_settled, start_date=start_date, end_date=end_date)
    return list(session.exec(stmt).all())


def get_record(session: Session, record_id: int) -> SalesRecord | None:
    return session.get(SalesRecord, record_id)


def create_record(session: Session, data: SalesRecordCreate) -> SalesRecord:
    record = SalesRecord.model_validate(data)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_record(session: Session, record_id: int, data: SalesRecordUpdate) -> SalesRecord | None:
    record = session.get(SalesRecord, record_id)
    if not record:
        return None
    record.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def delete_record(session: Session, record_id: int) -> bool:
    record = session.get(SalesRecord, record_id)
    if not record:
        return False
    session.delete(record)
    session.commit()
    return True


def get_summary(
    session: Session,
    customer_name: str | None = None,
    is_settled: bool | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    stmt = select(
        func.coalesce(func.sum(SalesRecord.amount), 0),
        func.coalesce(func.sum(SalesRecord.cost), 0),
    ).select_from(SalesRecord)
    stmt = _apply_filters(stmt, customer_name=customer_name, is_settled=is_settled, start_date=start_date, end_date=end_date)
    total_amount, total_cost = session.exec(stmt).one()
    total_amount = Decimal(str(total_amount))
    total_cost = Decimal(str(total_cost))
    total_profit = total_amount - total_cost
    avg_margin = float(total_profit / total_amount * 100) if total_amount else 0.0

    unsettled_stmt = select(func.count()).select_from(SalesRecord).where(col(SalesRecord.is_settled) == False)  # noqa: E712
    unsettled_stmt = _apply_filters(unsettled_stmt, customer_name=customer_name, is_settled=None, start_date=start_date, end_date=end_date)
    unsettled_count = session.exec(unsettled_stmt).one()

    return {
        "total_amount": total_amount,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "avg_margin": round(avg_margin, 2),
        "unsettled_count": unsettled_count,
    }
