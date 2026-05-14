from typing import NoReturn

from fastapi import HTTPException


def raise_not_found(detail: str) -> NoReturn:
    raise HTTPException(status_code=404, detail=detail)
