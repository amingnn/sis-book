from datetime import date
from decimal import Decimal

from sqlmodel import select

from app.orders import images as order_images
from app.orders.models import SalesOrder, SalesOrderCreate, SalesOrderItem, SalesOrderItemCreate, SalesOrderUpdate
from app.orders import service as orders_service
from app.product.models import Product
from app.sales.models import SalesRecord


def _item(product_name: str, total_boxes: int, per_box_qty: int, unit_price: str, image: str = ""):
    return SalesOrderItemCreate(
        product_name=product_name,
        total_boxes=total_boxes,
        per_box_qty=per_box_qty,
        unit_price=Decimal(unit_price),
        image=image,
    )


def _order_payload(**kwargs):
    payload = {
        "customer_name": "张三",
        "customer_phone": "13800000000",
        "delivery_address": "上海",
        "sales_date": date(2026, 4, 20),
        "delivery_date": date(2026, 4, 22),
        "payment_terms": "月结",
        "notes": "备注",
        "items": [
            _item("羽毛球", 2, 12, "10.50", image="raw-image"),
            _item("球拍", 1, 3, "88.00"),
        ],
    }
    payload.update(kwargs)
    return SalesOrderCreate(**payload)


def test_generate_order_number_increments_by_day(session):
    session.add(SalesOrder(order_number="MC20260420001", customer_name="A", sales_date=date(2026, 4, 20)))
    session.add(SalesOrder(order_number="MC20260420002", customer_name="B", sales_date=date(2026, 4, 20)))
    session.add(SalesOrder(order_number="MC20260421001", customer_name="C", sales_date=date(2026, 4, 21)))
    session.commit()

    assert orders_service._generate_order_number(session, date(2026, 4, 20)) == "MC20260420003"


def test_order_helpers_build_expected_values():
    items = [
        SalesOrderItem(product_name="  羽毛球  ", total_boxes=2, per_box_qty=12, unit_price=Decimal("10.50")),
        SalesOrderItem(product_name="球拍", total_boxes=1, per_box_qty=3, unit_price=Decimal("88")),
        SalesOrderItem(product_name="   ", total_boxes=1, per_box_qty=1, unit_price=Decimal("5")),
    ]
    order = SalesOrder(order_number="MC20260420001", customer_name="张三", sales_date=date(2026, 4, 20), notes="  加急  ")

    assert orders_service._calc_order_total(items) == Decimal("521.00")
    assert orders_service._build_order_product_summary(items) == "羽毛球 等2项"
    assert orders_service._build_order_sales_notes(order) == "开单单号：MC20260420001\n加急"


def test_create_order_creates_matching_sales_record(session):
    created = orders_service.create_order(session, _order_payload())
    sales_record = session.get(SalesRecord, created.sales_record_id)

    assert created.order_number == "MC20260420001"
    assert [item.image for item in created.items] == [
        "raw-image",
        "",
    ]
    assert sales_record is not None
    assert sales_record.customer_name == "张三"
    assert sales_record.product == "羽毛球 等2项"
    assert sales_record.amount == Decimal("516.00")
    assert sales_record.cost == Decimal("516.00")
    assert sales_record.payment_method == "月结"
    assert sales_record.notes == "开单单号：MC20260420001\n备注"


def test_create_order_stores_uploaded_item_image(session, tmp_path, monkeypatch):
    monkeypatch.setattr(order_images, "IMG_DIR", tmp_path / "img")
    uploaded_image = "data:image/jpeg;base64,aGVsbG8="

    created = orders_service.create_order(
        session,
        _order_payload(items=[_item("羽毛球", 1, 2, "10", image=uploaded_image)]),
    )

    assert created.items[0].image == "img/MC20260420001/羽毛球.jpg"
    assert (tmp_path / "img" / "MC20260420001" / "羽毛球.jpg").read_bytes() == b"hello"


def test_get_order_hydrates_missing_item_image_from_product_added_later(session):
    created = orders_service.create_order(
        session,
        _order_payload(items=[_item("羽毛球", 1, 2, "10")]),
    )
    session.add(Product(name="羽毛球", image="img/羽毛球.jpg"))
    session.commit()

    refreshed = orders_service.get_order(session, created.id)

    assert refreshed is not None
    assert refreshed.items[0].image == "img/羽毛球.jpg"


def test_update_order_reuses_sales_record_and_replaces_items(session):
    created = orders_service.create_order(session, _order_payload())
    sales_record_id = created.sales_record_id

    updated = orders_service.update_order(
        session,
        created.id,
        SalesOrderUpdate(
            customer_name="李四",
            customer_phone="13900000000",
            delivery_address="杭州",
            sales_date=date(2026, 4, 21),
            delivery_date=date(2026, 4, 23),
            payment_terms="现结",
            notes="已改单",
            items=[_item("足球", 1, 2, "50", image="new-image")],
        ),
    )
    sales_record = session.get(SalesRecord, sales_record_id)

    assert updated is not None
    assert updated.sales_record_id == sales_record_id
    assert len(updated.items) == 1
    assert updated.items[0].product_name == "足球"
    assert updated.items[0].image == "new-image"
    assert sales_record is not None
    assert sales_record.customer_name == "李四"
    assert sales_record.product == "足球"
    assert sales_record.amount == Decimal("100")
    assert sales_record.payment_method == "现结"
    assert sales_record.notes == f"开单单号：{updated.order_number}\n已改单"


def test_delete_order_removes_related_sales_record(session):
    created = orders_service.create_order(session, _order_payload())

    deleted = orders_service.delete_order(session, created.id)
    remaining_sales = session.exec(select(SalesRecord)).all()
    remaining_orders = session.exec(select(SalesOrder)).all()

    assert deleted is True
    assert remaining_sales == []
    assert remaining_orders == []
