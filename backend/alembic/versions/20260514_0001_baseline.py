"""baseline schema

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260514_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _column_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _create_index_if_missing(table_name: str, index_name: str, columns: list[str]) -> None:
    if index_name not in _index_names(table_name):
        op.create_index(index_name, table_name, columns)


def _create_customer() -> None:
    if _table_exists("customer"):
        return
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False, server_default=""),
        sa.Column("address", sa.String(), nullable=False, server_default=""),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def _create_sales_record() -> None:
    if _table_exists("salesrecord"):
        _add_column_if_missing("salesrecord", sa.Column("collection_time", sa.Date()))
        return
    op.create_table(
        "salesrecord",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_time", sa.Date(), nullable=False),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_time", sa.Date()),
        sa.Column("collection_time", sa.Date()),
        sa.Column("is_settled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("payment_method", sa.String(), nullable=False, server_default=""),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def _create_purchase_order() -> None:
    if _table_exists("purchaseorder"):
        _add_column_if_missing(
            "purchaseorder",
            sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        )
        return
    op.create_table(
        "purchaseorder",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_time", sa.Date(), nullable=False),
        sa.Column("supplier_name", sa.String(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("box_count", sa.Integer(), nullable=False),
        sa.Column("per_box_qty", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def _create_sales_order() -> None:
    if not _table_exists("salesorder"):
        op.create_table(
            "salesorder",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("order_number", sa.String(), nullable=False, server_default=""),
            sa.Column("customer_name", sa.String(), nullable=False),
            sa.Column("customer_phone", sa.String(), nullable=False, server_default=""),
            sa.Column("delivery_address", sa.String(), nullable=False, server_default=""),
            sa.Column("sales_date", sa.Date(), nullable=False),
            sa.Column("delivery_date", sa.Date()),
            sa.Column("payment_terms", sa.String(), nullable=False, server_default=""),
            sa.Column("notes", sa.String(), nullable=False, server_default=""),
            sa.Column("sales_record_id", sa.Integer()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if not _table_exists("salesorderitem"):
        op.create_table(
            "salesorderitem",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sales_order_id", sa.Integer(), sa.ForeignKey("salesorder.id"), nullable=False),
            sa.Column("product_name", sa.String(), nullable=False),
            sa.Column("color_spec", sa.String(), nullable=False, server_default=""),
            sa.Column("total_boxes", sa.Integer(), nullable=False),
            sa.Column("per_box_qty", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("box_size", sa.String(), nullable=False, server_default=""),
            sa.Column("notes", sa.String(), nullable=False, server_default=""),
            sa.Column("image", sa.String(), nullable=False, server_default=""),
        )
    else:
        _add_column_if_missing("salesorderitem", sa.Column("image", sa.String(), nullable=False, server_default=""))

    _backfill_order_item_image()


def _backfill_order_item_image() -> None:
    if not {"product_image", "id", "order_number"}.issubset(_column_names("salesorder")):
        return
    if not {"image", "id", "sales_order_id"}.issubset(_column_names("salesorderitem")):
        return
    op.get_bind().execute(
        text(
            """
            UPDATE salesorderitem
            SET image = (
                SELECT COALESCE(salesorder.product_image, '')
                FROM salesorder
                WHERE salesorder.id = salesorderitem.sales_order_id
            )
            WHERE COALESCE(image, '') = ''
              AND EXISTS (
                SELECT 1
                FROM salesorder
                WHERE salesorder.id = salesorderitem.sales_order_id
                  AND COALESCE(salesorder.product_image, '') != ''
              )
            """
        )
    )


def _create_task() -> None:
    if _table_exists("task"):
        return
    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("category", sa.String(), nullable=False, server_default="其他"),
        sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(), nullable=False, server_default="todo"),
        sa.Column("due_date", sa.Date()),
        sa.Column("related_type", sa.String(), nullable=False, server_default=""),
        sa.Column("related_id", sa.Integer()),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime()),
    )


def _create_supplier() -> None:
    if _table_exists("supplier"):
        return
    op.create_table(
        "supplier",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False, server_default=""),
        sa.Column("address", sa.String(), nullable=False, server_default=""),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def _create_product() -> None:
    if not _table_exists("product"):
        op.create_table(
            "product",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("image", sa.String(), nullable=False, server_default=""),
            sa.Column("per_box_qty", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("box_spec", sa.String(), nullable=False, server_default=""),
            sa.Column("volume", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
            sa.Column("purchase_price", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("stock_qty", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("notes", sa.String(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    else:
        _drop_product_supplier_name()


def _drop_product_supplier_name() -> None:
    if "supplier_name" not in _column_names("product"):
        return
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("supplier_name")


def _backfill_supplier_product_reference_data() -> None:
    conn = op.get_bind()
    if _table_exists("purchaseorder") and _table_exists("supplier"):
        _create_index_if_missing("supplier", "ix_supplier_name", ["name"])
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_supplier_summary"))
        conn.execute(
            text(
                """
                CREATE TEMPORARY TABLE _sis_book_supplier_summary AS
                SELECT DISTINCT TRIM(supplier_name) AS name
                FROM purchaseorder
                WHERE COALESCE(TRIM(supplier_name), '') != ''
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO supplier (name)
                SELECT name
                FROM _sis_book_supplier_summary
                WHERE NOT EXISTS (
                    SELECT 1 FROM supplier WHERE supplier.name = _sis_book_supplier_summary.name
                  )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_supplier_summary"))

    if not _table_exists("product"):
        return

    _create_index_if_missing("product", "ix_product_name", ["name"])

    if _table_exists("salesorderitem"):
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_order_product_summary"))
        conn.execute(
            text(
                """
                CREATE TEMPORARY TABLE _sis_book_order_product_summary AS
                SELECT
                    TRIM(product_name) AS name,
                    COALESCE(MAX(NULLIF(image, '')), '') AS image,
                    COALESCE(MAX(per_box_qty), 0) AS per_box_qty,
                    COALESCE(MAX(NULLIF(box_size, '')), '') AS box_spec,
                    0 - COALESCE(SUM(total_boxes * per_box_qty), 0) AS stock_qty
                FROM salesorderitem
                WHERE COALESCE(TRIM(product_name), '') != ''
                GROUP BY TRIM(product_name)
                """
            )
        )
        conn.execute(
            text("CREATE INDEX _sis_book_order_product_summary_name ON _sis_book_order_product_summary (name)")
        )
        conn.execute(
            text(
                """
                INSERT INTO product (name, image, per_box_qty, box_spec, stock_qty)
                SELECT
                    name,
                    image,
                    per_box_qty,
                    box_spec,
                    stock_qty
                FROM _sis_book_order_product_summary
                WHERE NOT EXISTS (
                    SELECT 1 FROM product WHERE product.name = _sis_book_order_product_summary.name
                  )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_order_product_summary"))

    if _table_exists("purchaseorder"):
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_purchase_product_summary"))
        conn.execute(
            text(
                """
                CREATE TEMPORARY TABLE _sis_book_purchase_product_summary AS
                SELECT
                    TRIM(product_name) AS name,
                    COALESCE(MAX(per_box_qty), 0) AS per_box_qty,
                    COALESCE(MAX(unit_price), 0) AS purchase_price,
                    COALESCE(SUM(box_count * per_box_qty), 0) AS stock_qty
                FROM purchaseorder
                WHERE COALESCE(TRIM(product_name), '') != ''
                GROUP BY TRIM(product_name)
                """
            )
        )
        conn.execute(
            text("CREATE INDEX _sis_book_purchase_product_summary_name ON _sis_book_purchase_product_summary (name)")
        )
        conn.execute(
            text(
                """
                INSERT INTO product (name, per_box_qty, purchase_price, stock_qty)
                SELECT
                    name,
                    per_box_qty,
                    purchase_price,
                    0
                FROM _sis_book_purchase_product_summary
                WHERE NOT EXISTS (
                    SELECT 1 FROM product WHERE product.name = _sis_book_purchase_product_summary.name
                  )
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE product
                SET
                    purchase_price = CASE
                        WHEN COALESCE(purchase_price, 0) = 0 THEN COALESCE(
                        (
                            SELECT purchase_price
                            FROM _sis_book_purchase_product_summary AS summary
                            WHERE summary.name = product.name
                        ),
                        0
                        )
                        ELSE purchase_price
                    END,
                    stock_qty = stock_qty + COALESCE(
                        (
                            SELECT stock_qty
                            FROM _sis_book_purchase_product_summary AS summary
                            WHERE summary.name = product.name
                        ),
                        0
                    )
                WHERE EXISTS (
                    SELECT 1
                    FROM _sis_book_purchase_product_summary AS summary
                    WHERE summary.name = product.name
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS _sis_book_purchase_product_summary"))


def upgrade() -> None:
    _create_customer()
    _create_sales_record()
    _create_purchase_order()
    _create_sales_order()
    _create_task()
    _create_supplier()
    _create_product()
    _backfill_supplier_product_reference_data()


def downgrade() -> None:
    for table_name in (
        "product",
        "supplier",
        "task",
        "salesorderitem",
        "salesorder",
        "purchaseorder",
        "salesrecord",
        "customer",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)
