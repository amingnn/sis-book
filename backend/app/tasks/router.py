from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.tasks import service
from app.tasks.models import TaskCreate, TaskQuickUpdate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.get("/summary")
def read_summary(session: Session = Depends(get_session)):
    return service.get_summary(session)


@router.get("", response_model=list[TaskResponse])
def read_tasks(
    keyword: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    due_only: bool = Query(False),
    session: Session = Depends(get_session),
):
    return service.list_tasks(session, keyword, status, priority, category, due_only)


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, session: Session = Depends(get_session)):
    if task := service.get_task(session, task_id):
        return task
    raise HTTPException(status_code=404, detail="任务不存在")


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, session: Session = Depends(get_session)):
    return service.create_task(session, data)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, session: Session = Depends(get_session)):
    if task := service.update_task(session, task_id, data):
        return task
    raise HTTPException(status_code=404, detail="任务不存在")


@router.patch("/{task_id}/status", response_model=TaskResponse)
def quick_update_status(
    task_id: int,
    data: TaskQuickUpdate,
    session: Session = Depends(get_session),
):
    if task := service.update_task(task_id=task_id, session=session, data=TaskUpdate(status=data.status)):
        return task
    raise HTTPException(status_code=404, detail="任务不存在")


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    if not service.delete_task(session, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
