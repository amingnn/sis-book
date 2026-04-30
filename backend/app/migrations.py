from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine, inspect, text

from app.orders.images import store_order_item_image


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable


def _ensure_migrations_table(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _migration_1_add_salesorderitem_image(conn) -> None:
    inspector = inspect(conn)
    columns = {column["name"] for column in inspector.get_columns("salesorderitem")}
    if "image" not in columns:
        conn.execute(
            text("ALTER TABLE salesorderitem ADD COLUMN image TEXT NOT NULL DEFAULT ''")
        )


def _migration_2_backfill_order_level_images(conn) -> None:
    inspector = inspect(conn)
    salesorder_columns = {column["name"] for column in inspector.get_columns("salesorder")}
    item_columns = {column["name"] for column in inspector.get_columns("salesorderitem")}
    if "product_image" not in salesorder_columns or "image" not in item_columns:
        return

    rows = conn.execute(
        text(
            """
            SELECT
                so.id AS order_id,
                so.order_number AS order_number,
                so.product_image AS product_image,
                soi.id AS item_id,
                soi.product_name AS product_name
            FROM salesorder AS so
            JOIN salesorderitem AS soi
              ON soi.id = (
                SELECT MIN(id) FROM salesorderitem WHERE sales_order_id = so.id
              )
            WHERE COALESCE(so.product_image, '') != ''
              AND COALESCE(soi.image, '') = ''
            """
        )
    ).mappings()

    for row in rows:
        relative_path = store_order_item_image(
            row["product_image"],
            row["order_number"] or f"order-{row['order_id']}",
            row["product_name"] or "item",
            0,
        )
        conn.execute(
            text("UPDATE salesorderitem SET image = :image WHERE id = :item_id"),
            {"image": relative_path, "item_id": row["item_id"]},
        )


def _migration_3_add_sales_collection_time(conn) -> None:
    inspector = inspect(conn)
    columns = {column["name"] for column in inspector.get_columns("salesrecord")}
    if "collection_time" not in columns:
        conn.execute(text("ALTER TABLE salesrecord ADD COLUMN collection_time DATE"))


def _migration_4_add_purchase_paid_amount(conn) -> None:
    inspector = inspect(conn)
    columns = {column["name"] for column in inspector.get_columns("purchaseorder")}
    if "paid_amount" not in columns:
        conn.execute(
            text(
                "ALTER TABLE purchaseorder ADD COLUMN paid_amount NUMERIC NOT NULL DEFAULT 0"
            )
        )


def _migration_5_create_task_table(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '其他',
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'todo',
                due_date DATE,
                related_type TEXT NOT NULL DEFAULT '',
                related_id INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
            """
        )
    )


def _migration_6_create_supplier_product_tables(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS supplier (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                image TEXT NOT NULL DEFAULT '',
                supplier_name TEXT NOT NULL DEFAULT '',
                per_box_qty INTEGER NOT NULL DEFAULT 0,
                box_spec TEXT NOT NULL DEFAULT '',
                volume NUMERIC NOT NULL DEFAULT 0,
                purchase_price NUMERIC NOT NULL DEFAULT 0,
                stock_qty INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    inspector = inspect(conn)
    tables = set(inspector.get_table_names())
    if "purchaseorder" in tables:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO supplier (name)
                SELECT DISTINCT TRIM(supplier_name)
                FROM purchaseorder
                WHERE COALESCE(TRIM(supplier_name), '') != ''
                """
            )
        )

    if "salesorderitem" in tables:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO product (
                    name,
                    image,
                    per_box_qty,
                    box_spec,
                    stock_qty
                )
                SELECT
                    TRIM(product_name),
                    COALESCE(MAX(NULLIF(image, '')), ''),
                    COALESCE(MAX(per_box_qty), 0),
                    COALESCE(MAX(NULLIF(box_size, '')), ''),
                    0 - COALESCE(SUM(total_boxes * per_box_qty), 0)
                FROM salesorderitem
                WHERE COALESCE(TRIM(product_name), '') != ''
                GROUP BY TRIM(product_name)
                """
            )
        )

    if "purchaseorder" in tables:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO product (
                    name,
                    supplier_name,
                    per_box_qty,
                    purchase_price,
                    stock_qty
                )
                SELECT
                    TRIM(product_name),
                    COALESCE(MAX(NULLIF(TRIM(supplier_name), '')), ''),
                    COALESCE(MAX(per_box_qty), 0),
                    COALESCE(MAX(unit_price), 0),
                    0
                FROM purchaseorder
                WHERE COALESCE(TRIM(product_name), '') != ''
                GROUP BY TRIM(product_name)
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE product
                SET
                    supplier_name = COALESCE(
                        NULLIF(supplier_name, ''),
                        (
                            SELECT po.supplier_name
                            FROM purchaseorder AS po
                            WHERE TRIM(po.product_name) = product.name
                              AND COALESCE(TRIM(po.supplier_name), '') != ''
                            ORDER BY po.purchase_time DESC, po.id DESC
                            LIMIT 1
                        ),
                        ''
                    ),
                    purchase_price = COALESCE(
                        NULLIF(purchase_price, 0),
                        (
                            SELECT po.unit_price
                            FROM purchaseorder AS po
                            WHERE TRIM(po.product_name) = product.name
                            ORDER BY po.purchase_time DESC, po.id DESC
                            LIMIT 1
                        ),
                        0
                    ),
                    stock_qty = stock_qty + COALESCE(
                        (
                            SELECT SUM(po.box_count * po.per_box_qty)
                            FROM purchaseorder AS po
                            WHERE TRIM(po.product_name) = product.name
                        ),
                        0
                    )
                WHERE EXISTS (
                    SELECT 1
                    FROM purchaseorder AS po
                    WHERE TRIM(po.product_name) = product.name
                )
                """
            )
        )


MIGRATIONS = [
    Migration(1, "add_salesorderitem_image", _migration_1_add_salesorderitem_image),
    Migration(2, "backfill_order_level_images", _migration_2_backfill_order_level_images),
    Migration(3, "add_sales_collection_time", _migration_3_add_sales_collection_time),
    Migration(4, "add_purchase_paid_amount", _migration_4_add_purchase_paid_amount),
    Migration(5, "create_task_table", _migration_5_create_task_table),
    Migration(6, "create_supplier_product_tables", _migration_6_create_supplier_product_tables),
]


def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        _ensure_migrations_table(conn)
        applied_versions = {
            row[0]
            for row in conn.execute(text("SELECT version FROM schema_migrations")).all()
        }

        for migration in MIGRATIONS:
            if migration.version in applied_versions:
                continue
            migration.apply(conn)
            conn.execute(
                text(
                    "INSERT INTO schema_migrations(version, name) VALUES (:version, :name)"
                ),
                {"version": migration.version, "name": migration.name},
            )
