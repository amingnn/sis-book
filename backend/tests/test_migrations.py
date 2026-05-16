from alembic import command
from sqlalchemy import create_engine, inspect, text

from app import database


BASELINE_REVISION = "20260514_0001"
HEAD_REVISION = "20260516_0002"


def _column_names(conn, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(conn).get_columns(table_name)}


def _index_names(conn, table_name: str) -> set[str]:
    return {index["name"] for index in inspect(conn).get_indexes(table_name)}


def _create_legacy_order_tables(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE salesorder (
                id INTEGER PRIMARY KEY,
                order_number TEXT,
                product_image TEXT
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE salesorderitem (
                id INTEGER PRIMARY KEY,
                sales_order_id INTEGER NOT NULL,
                product_name TEXT,
                total_boxes INTEGER NOT NULL DEFAULT 0,
                per_box_qty INTEGER NOT NULL DEFAULT 0,
                unit_price NUMERIC NOT NULL DEFAULT 0,
                color_spec TEXT NOT NULL DEFAULT '',
                box_size TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE salesrecord (
                id INTEGER PRIMARY KEY,
                sale_time DATE,
                customer_name TEXT,
                product TEXT,
                amount NUMERIC NOT NULL DEFAULT 0,
                delivery_time DATE,
                is_settled BOOLEAN NOT NULL DEFAULT 0,
                payment_method TEXT NOT NULL DEFAULT '',
                cost NUMERIC NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE purchaseorder (
                id INTEGER PRIMARY KEY,
                purchase_time DATE,
                supplier_name TEXT,
                product_name TEXT,
                box_count INTEGER NOT NULL DEFAULT 0,
                per_box_qty INTEGER NOT NULL DEFAULT 0,
                unit_price NUMERIC NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
    )


def test_alembic_baseline_migrates_legacy_schema_and_backfills_data(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        _create_legacy_order_tables(conn)
        conn.execute(
            text(
                "INSERT INTO salesorder(id, order_number, product_image) "
                "VALUES (1, 'MC20260420001', 'img/legacy-product.jpg')"
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO salesorderitem(
                    id,
                    sales_order_id,
                    product_name,
                    total_boxes,
                    per_box_qty,
                    unit_price,
                    box_size
                )
                VALUES (10, 1, '羽毛球', 2, 12, 3.5, '60*40*30')
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO purchaseorder(
                    id,
                    purchase_time,
                    supplier_name,
                    product_name,
                    box_count,
                    per_box_qty,
                    unit_price
                )
                VALUES (20, '2026-04-20', '胜利厂家', '羽毛球', 5, 12, 2.5)
                """
            )
        )

    database.run_alembic_migrations(engine)

    with engine.begin() as conn:
        inspector = inspect(conn)
        assert inspector.has_table("customer")
        assert inspector.has_table("supplier")
        assert inspector.has_table("product")
        assert inspector.has_table("task")
        assert "image" in _column_names(conn, "salesorderitem")
        assert "collection_time" in _column_names(conn, "salesrecord")
        assert "paid_amount" in _column_names(conn, "purchaseorder")
        assert "supplier_name" not in _column_names(conn, "product")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD_REVISION
        assert "ix_salesrecord_sale_time" in _index_names(conn, "salesrecord")
        assert "ix_salesrecord_settlement_collection" in _index_names(conn, "salesrecord")
        assert "ix_purchaseorder_purchase_time" in _index_names(conn, "purchaseorder")
        assert "ix_task_status_due_date" in _index_names(conn, "task")
        assert conn.execute(text("SELECT image FROM salesorderitem WHERE id = 10")).scalar_one() == "img/legacy-product.jpg"
        assert conn.execute(text("SELECT name FROM supplier")).scalar_one() == "胜利厂家"
        product = conn.execute(
            text(
                """
                SELECT image, per_box_qty, box_spec, purchase_price, stock_qty
                FROM product
                WHERE name = '羽毛球'
                """
            )
        ).one()
        assert product == ("img/legacy-product.jpg", 12, "60*40*30", 2.5, 36)


def test_alembic_migrations_are_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'idempotent.db'}")

    database.run_alembic_migrations(engine)
    database.run_alembic_migrations(engine)

    with engine.begin() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD_REVISION


def test_query_index_migration_can_downgrade_and_upgrade(tmp_path):
    db_path = tmp_path / "index-cycle.db"
    config = database.get_alembic_config(f"sqlite:///{db_path}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        assert "ix_salesrecord_sale_time" in _index_names(conn, "salesrecord")

    command.downgrade(config, BASELINE_REVISION)
    with engine.begin() as conn:
        assert "ix_salesrecord_sale_time" not in _index_names(conn, "salesrecord")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == BASELINE_REVISION

    command.upgrade(config, "head")
    with engine.begin() as conn:
        assert "ix_salesrecord_sale_time" in _index_names(conn, "salesrecord")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD_REVISION
    engine.dispose()


def test_alembic_baseline_drops_product_supplier_name_destructively(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'drop-product-supplier.db'}")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE product (
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
        conn.execute(
            text(
                """
                INSERT INTO product (
                    id,
                    name,
                    image,
                    supplier_name,
                    per_box_qty,
                    box_spec,
                    volume,
                    purchase_price,
                    stock_qty,
                    notes
                )
                VALUES (1, '羽毛球', 'img/product.jpg', '胜利厂家', 12, '60*40*30', 0.072, 2.5, 120, '热销')
                """
            )
        )

    database.run_alembic_migrations(engine)

    with engine.begin() as conn:
        assert "supplier_name" not in _column_names(conn, "product")
        product = conn.execute(
            text(
                """
                SELECT name, image, per_box_qty, box_spec, volume, purchase_price, stock_qty, notes
                FROM product
                WHERE id = 1
                """
            )
        ).one()
        assert product == ("羽毛球", "img/product.jpg", 12, "60*40*30", 0.072, 2.5, 120, "热销")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD_REVISION
