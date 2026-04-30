from fastapi import APIRouter

router = APIRouter(prefix="/api/import-export", tags=["导入导出"])


@router.get("/export/csv")
def export_csv():
    pass


@router.get("/export/pdf")
def export_pdf():
    pass


@router.post("/import/csv")
def import_csv():
    pass


@router.post("/import/excel")
def import_excel():
    pass
