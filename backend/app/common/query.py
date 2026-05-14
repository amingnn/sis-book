from typing import Any

from sqlmodel import col, or_


def apply_fuzzy_search(statement: Any, query: str | None, columns: list[Any]):
    if not query:
        return statement
    return statement.where(or_(*(col(column).contains(query) for column in columns)))
