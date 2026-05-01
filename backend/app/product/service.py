from datetime import datetime

from sqlmodel import Session, col, or_, select

from app.product.models import Product, ProductCreate, ProductUpdate


def list_products(session: Session, query: str | None = None) -> list[Product]:
    stmt = select(Product).order_by(col(Product.updated_at).desc())
    if query:
        stmt = stmt.where(
            or_(
                col(Product.name).contains(query),
                col(Product.box_spec).contains(query),
                col(Product.notes).contains(query),
            )
        )
    return list(session.exec(stmt).all())


def get_product(session: Session, product_id: int) -> Product | None:
    return session.get(Product, product_id)


def create_product(session: Session, data: ProductCreate) -> Product:
    product = Product.model_validate(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(session: Session, product_id: int, data: ProductUpdate) -> Product | None:
    product = session.get(Product, product_id)
    if not product:
        return None

    product.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    product.updated_at = datetime.now()
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: int) -> bool:
    product = session.get(Product, product_id)
    if not product:
        return False

    session.delete(product)
    session.commit()
    return True
