from datetime import datetime

from app.customer import service as customer_service
from app.customer.models import Customer, CustomerCreate, CustomerUpdate


def test_create_and_list_customers_orders_by_recent_update(session):
    older = Customer(
        name="旧客户",
        phone="13800000000",
        address="旧地址",
        notes="老客户",
        updated_at=datetime(2026, 1, 1, 9, 0, 0),
    )
    newer = Customer(
        name="新客户",
        phone="13900000000",
        address="新地址",
        notes="新客户",
        updated_at=datetime(2026, 1, 2, 9, 0, 0),
    )
    session.add(older)
    session.add(newer)
    session.commit()

    customers = customer_service.list_customers(session)

    assert [customer.name for customer in customers] == ["新客户", "旧客户"]


def test_list_customers_filters_by_query_across_customer_fields(session):
    session.add(
        Customer(
            name="张三",
            phone="13800000000",
            address="上海静安",
            notes="羽毛球馆客户",
        )
    )
    session.add(
        Customer(
            name="李四",
            phone="13900000000",
            address="杭州西湖",
            notes="长期客户",
        )
    )
    session.commit()

    assert [customer.name for customer in customer_service.list_customers(session, query="张")] == ["张三"]
    assert [customer.name for customer in customer_service.list_customers(session, query="139")] == ["李四"]
    assert [customer.name for customer in customer_service.list_customers(session, query="静安")] == ["张三"]
    assert [customer.name for customer in customer_service.list_customers(session, query="长期")] == ["李四"]


def test_create_get_update_and_delete_customer(session):
    created = customer_service.create_customer(
        session,
        CustomerCreate(
            name="默认客户",
            phone="13800000000",
            address="默认地址",
            notes="默认备注",
        ),
    )

    assert created.id is not None
    assert customer_service.get_customer(session, created.id).name == "默认客户"

    updated = customer_service.update_customer(
        session,
        created.id,
        CustomerUpdate(name="更新客户", phone="13900000000"),
    )

    assert updated is not None
    assert updated.name == "更新客户"
    assert updated.phone == "13900000000"
    assert updated.address == "默认地址"
    assert customer_service.delete_customer(session, created.id) is True
    assert customer_service.get_customer(session, created.id) is None


def test_update_customer_refreshes_updated_at(session):
    customer = Customer(
        name="待更新客户",
        updated_at=datetime(2026, 1, 1, 9, 0, 0),
    )
    session.add(customer)
    session.commit()
    original_updated_at = customer.updated_at

    assert customer.id is not None
    updated = customer_service.update_customer(
        session,
        customer.id,
        CustomerUpdate(notes="已更新"),
    )

    assert updated is not None
    assert updated.updated_at > original_updated_at


def test_update_customer_ignores_null_fields(session):
    customer = Customer(
        name="原客户",
        phone="13800000000",
        address="原地址",
        notes="原备注",
    )
    session.add(customer)
    session.commit()

    assert customer.id is not None
    updated = customer_service.update_customer(
        session,
        customer.id,
        CustomerUpdate(phone=None, address=None, notes=None),
    )

    assert updated is not None
    assert updated.name == "原客户"
    assert updated.phone == "13800000000"
    assert updated.address == "原地址"
    assert updated.notes == "原备注"
