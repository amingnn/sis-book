import sys
from pathlib import Path

import pytest
from sqlmodel import SQLModel, Session, create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.orders.models  # noqa: F401
import app.customer.models  # noqa: F401
import app.product.models  # noqa: F401
import app.purchases.models  # noqa: F401
import app.sales.models  # noqa: F401
import app.supplier.models  # noqa: F401
import app.tasks.models  # noqa: F401


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()
