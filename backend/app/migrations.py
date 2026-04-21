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


MIGRATIONS = [
    Migration(1, "add_salesorderitem_image", _migration_1_add_salesorderitem_image),
    Migration(2, "backfill_order_level_images", _migration_2_backfill_order_level_images),
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
