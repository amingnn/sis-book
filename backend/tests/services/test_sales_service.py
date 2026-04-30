from datetime import date
from decimal import Decimal

from app.sales.models import SalesRecord
from app.sales import service as sales_service


def _record(**kwargs):
    payload = {
        "sale_time": date(2026, 4, 20),
        "customer_name": "默认客户",
        "product": "羽毛球",
        "amount": Decimal("100"),
        "delivery_time": date(2026, 4, 21),
        "collection_time": None,
        "is_settled": False,
        "payment_method": "月结",
        "cost": Decimal("60"),
        "notes": "",
    }
    payload.update(kwargs)
    return SalesRecord(**payload)


def test_list_records_applies_combined_filters(session):
    session.add(
        _record(
            customer_name="目标客户",
            sale_time=date(2026, 4, 20),
            collection_time=date(2026, 4, 22),
            is_settled=False,
        )
    )
    session.add(
        _record(
            customer_name="目标客户",
            sale_time=date(2026, 4, 25),
            collection_time=date(2026, 4, 28),
            is_settled=False,
        )
    )
    session.add(
        _record(
            customer_name="其他客户",
            sale_time=date(2026, 4, 20),
            collection_time=date(2026, 4, 21),
            is_settled=False,
        )
    )
    session.commit()

    records = sales_service.list_records(
        session,
        customer_name="目标",
        is_settled=False,
        start_date=date(2026, 4, 18),
        end_date=date(2026, 4, 23),
        due_collection=True,
    )

    assert len(records) == 1
    assert records[0].customer_name == "目标客户"
    assert records[0].collection_time == date(2026, 4, 22)


def test_get_summary_returns_amount_cost_profit_margin_and_unsettled_count(session):
    session.add(
        _record(
            customer_name="甲",
            amount=Decimal("200"),
            cost=Decimal("120"),
            is_settled=False,
            collection_time=date(2026, 4, 18),
        )
    )
    session.add(
        _record(
            customer_name="乙",
            amount=Decimal("100"),
            cost=Decimal("80"),
            is_settled=True,
            collection_time=date(2026, 4, 30),
        )
    )
    session.commit()

    summary = sales_service.get_summary(session)

    assert summary == {
        "total_amount": Decimal("300"),
        "total_cost": Decimal("200"),
        "total_profit": Decimal("100"),
        "avg_margin": 33.33,
        "unsettled_count": 1,
    }


def test_get_due_collection_summary_returns_sorted_top_records(session):
    session.add(
        _record(
            customer_name="A",
            sale_time=date(2026, 4, 19),
            amount=Decimal("100"),
            collection_time=date(2026, 4, 21),
        )
    )
    session.add(
        _record(
            customer_name="B",
            sale_time=date(2026, 4, 22),
            amount=Decimal("200"),
            collection_time=date(2026, 4, 21),
        )
    )
    session.add(
        _record(
            customer_name="C",
            sale_time=date(2026, 4, 20),
            amount=Decimal("300"),
            collection_time=date(2026, 4, 20),
        )
    )
    session.add(
        _record(
            customer_name="D",
            sale_time=date(2026, 4, 20),
            amount=Decimal("999"),
            collection_time=date(2026, 4, 25),
        )
    )
    session.add(
        _record(
            customer_name="E",
            amount=Decimal("500"),
            collection_time=date(2026, 4, 21),
            is_settled=True,
        )
    )
    session.commit()

    summary = sales_service.get_due_collection_summary(session, date(2026, 4, 21))

    assert summary["due_collection_count"] == 3
    assert summary["due_collection_amount"] == 600.0
    assert [item["customer_name"] for item in summary["due_collection_records"]] == ["C", "B", "A"]
    assert summary["due_collection_records"][0]["collection_time"] == "2026-04-20"
