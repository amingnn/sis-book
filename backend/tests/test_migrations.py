from sqlalchemy import create_engine, inspect, text

from app import migrations


def _column_names(conn, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(conn).get_columns(table_name)}


def test_run_migrations_adds_missing_columns_backfills_data_and_records_versions(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    monkeypatch.setattr(migrations, "store_order_item_image", lambda *args: "img/migrated.png")

    with engine.begin() as conn:
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
        conn.execute(
            text(
                "INSERT INTO salesorder(id, order_number, product_image) VALUES (1, 'MC20260420001', 'data:image/png;base64,abc')"
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

    migrations.run_migrations(engine)

    with engine.begin() as conn:
        assert "image" in _column_names(conn, "salesorderitem")
        assert "collection_time" in _column_names(conn, "salesrecord")
        assert "paid_amount" in _column_names(conn, "purchaseorder")
        assert inspect(conn).has_table("task")
        assert inspect(conn).has_table("supplier")
        assert inspect(conn).has_table("product")
        assert conn.execute(text("SELECT image FROM salesorderitem WHERE id = 10")).scalar_one() == "img/migrated.png"
        assert conn.execute(text("SELECT name FROM supplier")).scalar_one() == "胜利厂家"
        product = conn.execute(
            text(
                """
                SELECT image, supplier_name, per_box_qty, box_spec, purchase_price, stock_qty
                FROM product
                WHERE name = '羽毛球'
                """
            )
        ).one()
        assert product == ("img/migrated.png", "胜利厂家", 12, "60*40*30", 2.5, 36)
        assert conn.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one() == 6


def test_run_migrations_is_idempotent(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations-idempotent.db'}")
    monkeypatch.setattr(migrations, "store_order_item_image", lambda *args: "img/migrated.png")

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE salesorder (id INTEGER PRIMARY KEY, order_number TEXT, product_image TEXT)"))
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

    migrations.run_migrations(engine)
    migrations.run_migrations(engine)

    with engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one() == 6
