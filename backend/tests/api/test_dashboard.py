import sys
import importlib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from app.dashboard.models import DashboardResponse
from app.purchases.models import PurchaseOrder
from app.sales.models import SalesRecord
from app.tasks.models import Task


def _load_main(monkeypatch, tmp_path):
    import app.config as config

    monkeypatch.setattr(config, "get_data_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "data.db")
    monkeypatch.setattr(config, "DATABASE_URL", f"sqlite:///{tmp_path / 'data.db'}")
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def test_get_base_dir_uses_project_root_in_dev_mode(monkeypatch, tmp_path):
    main = _load_main(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    assert main._get_base_dir() == Path(main.__file__).parent.parent


def test_get_base_dir_uses_meipass_when_frozen(monkeypatch, tmp_path):
    main = _load_main(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "/tmp/frozen-app", raising=False)

    assert main._get_base_dir() == Path("/tmp/frozen-app")


def test_get_dashboard_handles_empty_database(session, monkeypatch, tmp_path):
    main = _load_main(monkeypatch, tmp_path)

    dashboard = main.get_dashboard(session)
    validated_dashboard = DashboardResponse.model_validate(dashboard)

    assert validated_dashboard.month_sales == 0.0
    assert validated_dashboard.month_profit_margin == 0.0
    assert len(validated_dashboard.month_trend) == 6
    assert validated_dashboard.top_products == []
    assert validated_dashboard.top_customers == []
    assert validated_dashboard.top_suppliers == []
    assert validated_dashboard.task_summary.open_count == 0
    assert validated_dashboard.action_items == []


def test_get_dashboard_returns_aggregated_stats(session, monkeypatch, tmp_path):
    main = _load_main(monkeypatch, tmp_path)
    today = date.today()
    session.add(
        SalesRecord(
            sale_time=today,
            customer_name="本月客户",
            product="羽毛球",
            amount=Decimal("300"),
            delivery_time=today,
            collection_time=today,
            is_settled=False,
            payment_method="月结",
            cost=Decimal("200"),
        )
    )
    session.add(
        SalesRecord(
            sale_time=date(today.year, 1, 15),
            customer_name="年内客户",
            product="球拍",
            amount=Decimal("200"),
            delivery_time=today,
            collection_time=None,
            is_settled=True,
            payment_method="现结",
            cost=Decimal("100"),
        )
    )
    session.add(
        SalesRecord(
            sale_time=date(today.year - 1, 12, 31),
            customer_name="去年客户",
            product="旧商品",
            amount=Decimal("999"),
            delivery_time=today,
            collection_time=None,
            is_settled=False,
            payment_method="现结",
            cost=Decimal("500"),
        )
    )
    session.add(
        PurchaseOrder(
            purchase_time=today,
            supplier_name="供货商甲",
            product_name="羽毛球",
            box_count=2,
            per_box_qty=12,
            unit_price=Decimal("8.5"),
            paid_amount=Decimal("0"),
        )
    )
    session.add(
        PurchaseOrder(
            purchase_time=date(today.year, max(1, today.month - 1), 1),
            supplier_name="供货商乙",
            product_name="球拍",
            box_count=1,
            per_box_qty=5,
            unit_price=Decimal("20"),
            paid_amount=Decimal("50"),
        )
    )
    session.add(
        Task(
            title="联系客户确认回款",
            priority="high",
            status="todo",
            due_date=today - timedelta(days=1),
        )
    )
    session.commit()

    dashboard = main.get_dashboard(session)
    validated_dashboard = DashboardResponse.model_validate(dashboard)

    assert dashboard["month_sales"] == 300.0
    assert validated_dashboard.month_sales == 300.0
    assert dashboard["month_cost"] == 200.0
    assert dashboard["month_profit"] == 100.0
    assert dashboard["year_sales"] == 500.0
    assert dashboard["year_cost"] == 300.0
    assert dashboard["year_profit"] == 200.0
    assert dashboard["month_profit_margin"] == 33.33
    assert dashboard["year_profit_margin"] == 40.0
    assert dashboard["unsettled_count"] == 2
    assert dashboard["unsettled_amount"] == 1299.0
    assert dashboard["due_collection_count"] == 1
    assert dashboard["due_collection_amount"] == 300.0
    assert dashboard["month_trend"][-1]["sales"] == 300.0
    assert dashboard["month_trend"][-1]["profit"] == 100.0
    assert dashboard["top_products"][0]["name"] == "羽毛球"
    assert dashboard["top_customers"][0]["name"] == "本月客户"
    assert dashboard["top_suppliers"][0]["name"] == "供货商甲"
    assert dashboard["task_summary"]["open_count"] == 1
    assert dashboard["task_summary"]["overdue_count"] == 1
    assert dashboard["action_items"][0]["type"] == "collection"
    assert dashboard["action_items"][0]["target"].startswith("/sales?")
    assert "due=collection" in dashboard["action_items"][0]["target"]
    assert "customer_name=" in dashboard["action_items"][0]["target"]
    assert "product=" in dashboard["action_items"][0]["target"]
    assert dashboard["action_items"][1]["type"] == "task"
    assert dashboard["action_items"][1]["target"].startswith("/tasks?keyword=")
    assert dashboard["recent_sales"][0]["customer_name"] == "本月客户"
    assert dashboard["recent_sales"][0]["sale_time"] == today.isoformat()
    assert dashboard["recent_sales"][0]["gross_profit"] == 100.0
    assert dashboard["recent_purchases"][0]["supplier_name"] == "供货商甲"
    assert dashboard["recent_purchases"][0]["total_amount"] == 204.0
