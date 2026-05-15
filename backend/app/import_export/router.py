from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.import_export import service

router = APIRouter(prefix="/api/import-export", tags=["导入导出"])


class ExportExcelPayload(BaseModel):
    target_dir: str = ""


@router.post("/export/excel")
def export_excel(
    payload: ExportExcelPayload,
    session: Session = Depends(get_session),
):
    try:
        return service.export_excel(session, payload.target_dir)
    except service.ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/excel/preview")
async def preview_excel(request: Request):
    try:
        return service.preview_excel(await request.body())
    except service.ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/excel")
async def import_excel(
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return service.import_excel(session, await request.body())
    except service.ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
