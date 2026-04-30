from datetime import date, datetime

from app.tasks.models import Task, TaskCreate, TaskUpdate
from app.tasks import service as tasks_service


class FrozenDateTime(datetime):
    @classmethod
    def now(cls):
        return cls(2026, 4, 23, 12, 0, 0)


def test_create_task_sets_completed_at_for_done_status(session, monkeypatch):
    monkeypatch.setattr(tasks_service, "datetime", FrozenDateTime)

    task = tasks_service.create_task(session, TaskCreate(title="已完成任务", status="done"))

    assert task.completed_at == FrozenDateTime(2026, 4, 23, 12, 0, 0)


def test_update_task_sets_and_clears_completed_at_on_status_change(session, monkeypatch):
    monkeypatch.setattr(tasks_service, "datetime", FrozenDateTime)
    task = Task(title="待办任务", status="todo")
    session.add(task)
    session.commit()

    finished = tasks_service.update_task(session, task.id, TaskUpdate(status="done"))
    assert finished is not None
    assert finished.completed_at == FrozenDateTime(2026, 4, 23, 12, 0, 0)

    reopened = tasks_service.update_task(session, task.id, TaskUpdate(status="doing"))

    assert reopened is not None
    assert reopened.completed_at is None


def test_get_summary_returns_counts_overdue_and_recent_tasks(session, monkeypatch):
    monkeypatch.setattr(tasks_service, "datetime", FrozenDateTime)
    session.add(
        Task(
            title="最旧任务",
            status="todo",
            due_date=date(2026, 4, 20),
            created_at=datetime(2026, 4, 20, 10, 0, 0),
        )
    )
    session.add(
        Task(
            title="进行中任务",
            status="doing",
            due_date=date(2026, 4, 24),
            created_at=datetime(2026, 4, 22, 10, 0, 0),
        )
    )
    session.add(
        Task(
            title="已完成任务",
            status="done",
            created_at=datetime(2026, 4, 23, 9, 0, 0),
        )
    )
    session.commit()

    summary = tasks_service.get_summary(session)

    assert summary["total_count"] == 3
    assert summary["todo_count"] == 1
    assert summary["doing_count"] == 1
    assert summary["done_count"] == 1
    assert summary["overdue_count"] == 1
    assert [task["title"] for task in summary["recent_tasks"]] == [
        "已完成任务",
        "进行中任务",
        "最旧任务",
    ]
