from sqlmodel import Session, col, select

from app.common.crud import create_entity, delete_entity, get_entity, update_entity
from app.common.query import apply_fuzzy_search
from app.product.models import Product, ProductCreate, ProductUpdate


def list_products(session: Session, query: str | None = None) -> list[Product]:
    stmt = select(Product).order_by(col(Product.updated_at).desc())
    stmt = apply_fuzzy_search(stmt, query, [Product.name, Product.box_spec, Product.notes])
    return list(session.exec(stmt).all())


def get_product(session: Session, product_id: int) -> Product | None:
    return get_entity(session, Product, product_id)


def create_product(session: Session, data: ProductCreate) -> Product:
    return create_entity(session, Product, data)


def update_product(session: Session, product_id: int, data: ProductUpdate) -> Product | None:
    product = session.get(Product, product_id)
    if not product:
        return None

    return update_entity(session, product, data)


def delete_product(session: Session, product_id: int) -> bool:
    product = session.get(Product, product_id)
    if not product:
        return False

    delete_entity(session, product)
    return True
