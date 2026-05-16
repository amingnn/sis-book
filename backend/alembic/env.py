from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.config import DATABASE_URL
from app.logging import configure_logging

import app.customer.models  # noqa: F401
import app.orders.models  # noqa: F401
import app.product.models  # noqa: F401
import app.purchases.models  # noqa: F401
import app.sales.models  # noqa: F401
import app.supplier.models  # noqa: F401
import app.tasks.models  # noqa: F401

config = context.config
if config.get_main_option("sqlalchemy.url") == "sqlite:///data/data.db":
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

configure_logging()

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
