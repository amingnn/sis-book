from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, func, select
from sqlmodel import or_

from app.sales.models import SalesRecord, SalesRecordCreate, SalesRecordUpdate


def _apply_filters(
    statement,
    *,
    q: str | None = None,
    customer_name: str | None = None,
    product: str | None = None,
    is_settled: bool | None = None,
    payment_method: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    due_collection: bool = False,
    due_date: date | None = None,
):
    if q:
        statement = statement.where(
            or_(
                col(SalesRecord.customer_name).contains(q),
                col(SalesRecord.product).contains(q),
                col(SalesRecord.payment_method).contains(q),
                col(SalesRecord.notes).contains(q),
            )
        )
    if customer_name:
        statement = statement.where(col(SalesRecord.customer_name).contains(customer_name))
    if product:
        statement = statement.where(col(SalesRecord.product).contains(product))
    if payment_method:
        statement = statement.where(col(SalesRecord.payment_method).contains(payment_method))
    if is_settled is not None:
        statement = statement.where(col(SalesRecord.is_settled) == is_settled)
    if start_date:
        statement = statement.where(col(SalesRecord.sale_time) >= start_date)
    if end_date:
        statement = statement.where(col(SalesRecord.sale_time) <= end_date)
    if due_collection:
        target_date = due_date or date.today()
        statement = statement.where(col(SalesRecord.is_settled) == False)  # noqa: E712
        statement = statement.where(col(SalesRecord.collection_time).is_not(None))
        statement = statement.where(col(SalesRecord.collection_time) <= target_date)
    return statement


def list_records(
    session: Session,
    q: str | None = None,
    customer_name: str | None = None,
    product: str | None = None,
    is_settled: bool | None = None,
    payment_method: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    due_collection: bool = False,
) -> list[SalesRecord]:
    stmt = select(SalesRecord).order_by(col(SalesRecord.sale_time).desc())
    stmt = _apply_filters(
        stmt,
        q=q,
        customer_name=customer_name,
        product=product,
        is_settled=is_settled,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        due_collection=due_collection,
    )
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
    q: str | None = None,
    customer_name: str | None = None,
    product: str | None = None,
    is_settled: bool | None = None,
    payment_method: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    due_collection: bool = False,
) -> dict:
    stmt = select(
        func.coalesce(func.sum(SalesRecord.amount), 0),
        func.coalesce(func.sum(SalesRecord.cost), 0),
    ).select_from(SalesRecord)
    stmt = _apply_filters(
        stmt,
        q=q,
        customer_name=customer_name,
        product=product,
        is_settled=is_settled,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        due_collection=due_collection,
    )
    total_amount, total_cost = session.exec(stmt).one()
    total_amount = Decimal(str(total_amount))
    total_cost = Decimal(str(total_cost))
    total_profit = total_amount - total_cost
    avg_margin = float(total_profit / total_amount * 100) if total_amount else 0.0

    unsettled_stmt = select(func.count()).select_from(SalesRecord).where(col(SalesRecord.is_settled) == False)  # noqa: E712
    unsettled_stmt = _apply_filters(
        unsettled_stmt,
        q=q,
        customer_name=customer_name,
        product=product,
        is_settled=None,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        due_collection=due_collection,
    )
    unsettled_count = session.exec(unsettled_stmt).one()

    return {
        "total_amount": total_amount,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "avg_margin": round(avg_margin, 2),
        "unsettled_count": unsettled_count,
    }


def get_due_collection_summary(session: Session, due_date: date) -> dict:
    stmt = (
        select(
            func.count(col(SalesRecord.id)),
            func.coalesce(func.sum(SalesRecord.amount), 0),
        )
        .where(col(SalesRecord.is_settled) == False)  # noqa: E712
        .where(col(SalesRecord.collection_time).is_not(None))
        .where(col(SalesRecord.collection_time) <= due_date)
    )
    due_count, due_amount = session.exec(stmt).one()

    due_records = session.exec(
        select(SalesRecord)
        .where(col(SalesRecord.is_settled) == False)  # noqa: E712
        .where(col(SalesRecord.collection_time).is_not(None))
        .where(col(SalesRecord.collection_time) <= due_date)
        .order_by(col(SalesRecord.collection_time).asc(), col(SalesRecord.sale_time).desc())
        .limit(5)
    ).all()

    return {
        "due_collection_count": due_count,
        "due_collection_amount": float(Decimal(str(due_amount))),
        "due_collection_records": [
            {
                "id": record.id,
                "customer_name": record.customer_name,
                "product": record.product,
                "amount": float(record.amount),
                "collection_time": record.collection_time.isoformat() if record.collection_time else None,
            }
            for record in due_records
        ],
    }
