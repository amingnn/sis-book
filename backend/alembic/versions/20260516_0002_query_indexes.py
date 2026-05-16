"""add query indexes

Revision ID: 20260516_0002
Revises: 20260514_0001
Create Date: 2026-05-16
"""

from alembic import op
from sqlalchemy import inspect

revision = "20260516_0002"
down_revision = "20260514_0001"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(index["name"] == index_name for index in inspect(op.get_bind()).get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if _table_exists(table_name) and not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    _create_index_if_missing("ix_salesrecord_sale_time", "salesrecord", ["sale_time"])
    _create_index_if_missing(
        "ix_salesrecord_settlement_collection",
        "salesrecord",
        ["is_settled", "collection_time"],
    )
    _create_index_if_missing("ix_salesrecord_customer_name", "salesrecord", ["customer_name"])
    _create_index_if_missing("ix_salesrecord_product", "salesrecord", ["product"])
    _create_index_if_missing("ix_purchaseorder_purchase_time", "purchaseorder", ["purchase_time"])
    _create_index_if_missing("ix_purchaseorder_supplier_name", "purchaseorder", ["supplier_name"])
    _create_index_if_missing("ix_purchaseorder_product_name", "purchaseorder", ["product_name"])
    _create_index_if_missing("ix_task_status_due_date", "task", ["status", "due_date"])


def downgrade() -> None:
    _drop_index_if_exists("ix_task_status_due_date", "task")
    _drop_index_if_exists("ix_purchaseorder_product_name", "purchaseorder")
    _drop_index_if_exists("ix_purchaseorder_supplier_name", "purchaseorder")
    _drop_index_if_exists("ix_purchaseorder_purchase_time", "purchaseorder")
    _drop_index_if_exists("ix_salesrecord_product", "salesrecord")
    _drop_index_if_exists("ix_salesrecord_customer_name", "salesrecord")
    _drop_index_if_exists("ix_salesrecord_settlement_collection", "salesrecord")
    _drop_index_if_exists("ix_salesrecord_sale_time", "salesrecord")
