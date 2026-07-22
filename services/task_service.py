from datetime import datetime, time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.task import Task
from models.user import User
from services.time_service import now_local


def create_task(
    db: Session,
    user_id: int,
    title: str,
    description: Optional[str],
    priority: str,
    deadline: datetime
) -> Task:
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        priority=priority,
        status="Pending",
        deadline=deadline,
        reminder_sent=False,
        reminder_preset="default"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    from services.reminder_service import create_reminders_for_task
    create_reminders_for_task(db, task)

    return task


def get_tasks_for_user(
    db: Session,
    telegram_id: int
) -> List[Task]:
    return (
        db.query(Task)
        .join(User)
        .filter(
            User.telegram_id == telegram_id,
            Task.status == "Pending"
        )
        .order_by(Task.deadline.asc())
        .all()
    )


def get_today_tasks(
    db: Session,
    telegram_id: int
) -> List[Task]:
    today = now_local().date()
    day_start = datetime.combine(today, time.min)
    day_end = datetime.combine(today, time.max)

    return (
        db.query(Task)
        .join(User)
        .filter(
            User.telegram_id == telegram_id,
            Task.status == "Pending",
            Task.deadline >= day_start,
            Task.deadline <= day_end
        )
        .order_by(Task.deadline.asc())
        .all()
    )


def get_task_for_user(
    db: Session,
    task_id: int,
    telegram_id: int
) -> Optional[Task]:
    return (
        db.query(Task)
        .join(User)
        .filter(
            Task.id == task_id,
            User.telegram_id == telegram_id
        )
        .first()
    )


def complete_task(
    db: Session,
    task_id: int,
    telegram_id: int
) -> Optional[Task]:
    task = get_task_for_user(db, task_id, telegram_id)

    if task is None:
        return None

    task.status = "Completed"
    task.completed_at = now_local()

    db.commit()
    db.refresh(task)

    from services.reminder_service import remove_pending_reminders
    remove_pending_reminders(db, task.id)

    return task


def delete_task(
    db: Session,
    task_id: int,
    telegram_id: int
) -> bool:
    task = get_task_for_user(db, task_id, telegram_id)

    if task is None:
        return False

    from services.reminder_service import remove_all_task_reminders
    remove_all_task_reminders(db, task.id)

    db.delete(task)
    db.commit()

    return True


def update_task(
    db: Session,
    task_id: int,
    telegram_id: int,
    **changes: Any
) -> Optional[Task]:
    task = get_task_for_user(db, task_id, telegram_id)

    if task is None:
        return None

    allowed_fields = {
        "title",
        "description",
        "deadline",
        "priority",
    }

    deadline_changed = "deadline" in changes

    for field_name, value in changes.items():
        if field_name in allowed_fields:
            setattr(task, field_name, value)

    if deadline_changed:
        task.reminder_sent = False

    db.commit()
    db.refresh(task)

    if deadline_changed:
        from services.reminder_service import create_reminders_for_task
        create_reminders_for_task(db, task)

    return task


def get_statistics(
    db: Session,
    telegram_id: int
) -> Dict[str, int]:
    base_query = (
        db.query(Task)
        .join(User)
        .filter(User.telegram_id == telegram_id)
    )

    total = base_query.count()
    pending = base_query.filter(Task.status == "Pending").count()
    completed = base_query.filter(Task.status == "Completed").count()
    overdue = base_query.filter(
        Task.status == "Pending",
        Task.deadline < now_local()
    ).count()

    completion_rate = (
        round((completed / total) * 100)
        if total > 0
        else 0
    )

    return {
        "total": total,
        "pending": pending,
        "completed": completed,
        "overdue": overdue,
        "completion_rate": completion_rate,
    }
