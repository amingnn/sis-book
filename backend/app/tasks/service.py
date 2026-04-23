from datetime import datetime

from sqlmodel import Session, col, select

from app.tasks.models import Task, TaskCreate, TaskUpdate


def _apply_filters(
    statement,
    *,
    keyword: str | None,
    status: str | None,
    priority: str | None,
    category: str | None,
    due_only: bool,
):
    if keyword:
        statement = statement.where(
            col(Task.title).contains(keyword) | col(Task.description).contains(keyword)
        )
    if status:
        statement = statement.where(col(Task.status) == status)
    if priority:
        statement = statement.where(col(Task.priority) == priority)
    if category:
        statement = statement.where(col(Task.category) == category)
    if due_only:
        statement = statement.where(col(Task.due_date).is_not(None))
    return statement


def list_tasks(
    session: Session,
    keyword: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    due_only: bool = False,
) -> list[Task]:
    stmt = select(Task).order_by(
        col(Task.status).asc(),
        col(Task.priority).desc(),
        col(Task.due_date).asc(),
        col(Task.created_at).desc(),
    )
    stmt = _apply_filters(
        stmt,
        keyword=keyword,
        status=status,
        priority=priority,
        category=category,
        due_only=due_only,
    )
    return list(session.exec(stmt).all())


def get_task(session: Session, task_id: int) -> Task | None:
    return session.get(Task, task_id)


def create_task(session: Session, data: TaskCreate) -> Task:
    task = Task.model_validate(data)
    if task.status == "done":
        task.completed_at = datetime.now()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(session: Session, task_id: int, data: TaskUpdate) -> Task | None:
    task = session.get(Task, task_id)
    if not task:
        return None

    update_data = data.model_dump(exclude_unset=True)
    next_status = update_data.get("status")
    if next_status is not None and next_status != task.status:
        if next_status == "done":
            update_data["completed_at"] = datetime.now()
        else:
            update_data["completed_at"] = None

    task.sqlmodel_update(update_data)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: int) -> bool:
    task = session.get(Task, task_id)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True


def get_summary(session: Session) -> dict:
    tasks = list(session.exec(select(Task)).all())
    today = datetime.now().date()

    total_count = len(tasks)
    todo_count = sum(1 for task in tasks if task.status == "todo")
    doing_count = sum(1 for task in tasks if task.status == "doing")
    done_count = sum(1 for task in tasks if task.status == "done")
    overdue_count = sum(
        1
        for task in tasks
        if task.status != "done" and task.due_date is not None and task.due_date < today
    )

    recent_tasks = sorted(tasks, key=lambda task: task.created_at, reverse=True)[:5]

    return {
        "total_count": total_count,
        "todo_count": todo_count,
        "doing_count": doing_count,
        "done_count": done_count,
        "overdue_count": overdue_count,
        "recent_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "category": task.category,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in recent_tasks
        ],
    }
