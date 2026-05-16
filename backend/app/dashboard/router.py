from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dashboard.models import DashboardResponse
from app.dashboard.service import get_dashboard
from app.database import get_session

router = APIRouter(prefix="/api", tags=["首页"])


@router.get("/dashboard", response_model=DashboardResponse)
def read_dashboard(session: Session = Depends(get_session)):
    return get_dashboard(session)
