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
                SELECT image, per_box_qty, box_spec, purchase_price, stock_qty
                FROM product
                WHERE name = '羽毛球'
                """
            )
        ).one()
        assert product == ("img/migrated.png", 12, "60*40*30", 2.5, 36)
        assert "supplier_name" not in _column_names(conn, "product")
        assert conn.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one() == 7


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
        assert conn.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one() == 7


def test_run_migrations_drops_product_supplier_name_destructively(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations-drop-product-supplier.db'}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        for version in range(1, 7):
            conn.execute(
                text("INSERT INTO schema_migrations(version, name) VALUES (:version, :name)"),
                {"version": version, "name": f"migration_{version}"},
            )
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
                VALUES (1, '羽毛球', 'img/product.png', '胜利厂家', 12, '60*40*30', 0.072, 2.5, 120, '热销')
                """
            )
        )

    migrations.run_migrations(engine)

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
        assert product == ("羽毛球", "img/product.png", 12, "60*40*30", 0.072, 2.5, 120, "热销")
        assert conn.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one() == 7
