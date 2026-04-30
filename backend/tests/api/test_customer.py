import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.customer.models import Customer
from app.customer import router as customer_router


def test_customer_router_crud(session):
    created = customer_router.create_customer(
        customer_router.CustomerCreate(
            name="张三",
            phone="13800000000",
            address="上海静安",
            notes="羽毛球馆客户",
        ),
        session,
    )

    assert created.name == "张三"
    assert created.phone == "13800000000"

    customer_id = created.id
    assert customer_id is not None, "创建的客户应该有 ID"
    found = customer_router.read_customer(customer_id, session)
    assert found.address == "上海静安"

    old_updated_at = found.updated_at
    updated = customer_router.update_customer(
        customer_id,
        customer_router.CustomerUpdate(name="张三丰", notes="重点客户"),
        session,
    )

    assert updated.name == "张三丰"
    assert updated.notes == "重点客户"
    assert updated.updated_at > old_updated_at, "updated_at 应该在更新后改变"

    assert customer_router.delete_customer(customer_id, session) is None

    with pytest.raises(HTTPException) as exc_info:
        customer_router.read_customer(customer_id, session)
    assert exc_info.value.status_code == 404


def test_customer_router_lists_and_filters_customers(session):
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

    customers = customer_router.read_customers(q=None, session=session)
    search_result = customer_router.read_customers(q="长期", session=session)

    assert {customer.name for customer in customers} == {"张三", "李四"}
    assert [customer.name for customer in search_result] == ["李四"]


def test_customer_router_returns_404_for_missing_customer(session):
    with pytest.raises(HTTPException) as get_exc_info:
        customer_router.read_customer(999, session)
    assert get_exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as update_exc_info:
        customer_router.update_customer(
            999,
            customer_router.CustomerUpdate(name="不存在"),
            session,
        )
    assert update_exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as delete_exc_info:
        customer_router.delete_customer(999, session)
    assert delete_exc_info.value.status_code == 404


def test_customer_router_rejects_empty_name(session):
    with pytest.raises(ValidationError):
        customer_router.create_customer(
            customer_router.CustomerCreate(name="   "),
            session,
        )

    customer = Customer(name="原客户")
    session.add(customer)
    session.commit()

    assert customer.id is not None
    with pytest.raises(ValidationError):
        customer_router.update_customer(
            customer.id,
            customer_router.CustomerUpdate(name=""),
            session,
        )

    with pytest.raises(ValidationError):
        customer_router.update_customer(
            customer.id,
            customer_router.CustomerUpdate(name=None),
            session,
        )
