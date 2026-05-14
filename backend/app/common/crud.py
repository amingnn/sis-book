from datetime import datetime
from typing import Any, TypeVar

from sqlmodel import Session, SQLModel

ModelT = TypeVar("ModelT", bound=SQLModel)


def create_entity(session: Session, model_class: type[ModelT], data: SQLModel) -> ModelT:
    entity = model_class.model_validate(data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


def update_entity(
    session: Session,
    entity: ModelT,
    data: SQLModel,
    *,
    exclude_none: bool = True,
    touch_updated_at: bool = True,
) -> ModelT:
    entity.sqlmodel_update(
        data.model_dump(exclude_unset=True, exclude_none=exclude_none)
    )
    if touch_updated_at and hasattr(entity, "updated_at"):
        setattr(entity, "updated_at", datetime.now())
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


def delete_entity(session: Session, entity: SQLModel) -> None:
    session.delete(entity)
    session.commit()


def get_entity(session: Session, model_class: type[ModelT], entity_id: Any) -> ModelT | None:
    return session.get(model_class, entity_id)
