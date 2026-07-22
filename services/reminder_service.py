from datetime import timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from config import parse_default_reminder_offsets
from models.reminder import Reminder
from models.task import Task
from models.user import User
from services.time_service import now_local


REMINDER_PRESETS = {
    "default": parse_default_reminder_offsets(),
    "hour": [60, 0],
    "deadline": [0],
    "none": [],
}

REMINDER_PRESET_NAMES = {
    "default": "За день, за годину та в момент дедлайну",
    "hour": "За годину та в момент дедлайну",
    "deadline": "Лише в момент дедлайну",
    "none": "Без нагадувань",
}


def reminder_offset_to_text(offset_minutes: int) -> str:
    if offset_minutes == 0:
        return "Настав дедлайн"

    if offset_minutes % 1440 == 0:
        days = offset_minutes // 1440
        return f"До дедлайну: {days} дн."

    if offset_minutes % 60 == 0:
        hours = offset_minutes // 60
        return f"До дедлайну: {hours} год."

    return f"До дедлайну: {offset_minutes} хв."


def replace_task_reminders(
    db: Session,
    task: Task,
    offsets: List[int]
) -> None:
    (
        db.query(Reminder)
        .filter(
            Reminder.task_id == task.id,
            Reminder.sent_at.is_(None)
        )
        .delete(synchronize_session=False)
    )

    current_time = now_local()

    for offset in sorted(set(offsets), reverse=True):
        remind_at = task.deadline - timedelta(minutes=offset)

        if remind_at <= current_time:
            continue

        db.add(
            Reminder(
                task_id=task.id,
                offset_minutes=offset,
                remind_at=remind_at
            )
        )

    db.commit()


def create_reminders_for_task(
    db: Session,
    task: Task
) -> None:
    offsets = REMINDER_PRESETS.get(
        task.reminder_preset,
        REMINDER_PRESETS["default"]
    )
    replace_task_reminders(db, task, offsets)


def set_task_reminder_preset(
    db: Session,
    task_id: int,
    telegram_id: int,
    preset: str
) -> Optional[Task]:
    if preset not in REMINDER_PRESETS:
        return None

    task = (
        db.query(Task)
        .join(User)
        .filter(
            Task.id == task_id,
            User.telegram_id == telegram_id
        )
        .first()
    )

    if task is None:
        return None

    task.reminder_preset = preset
    db.commit()
    db.refresh(task)

    replace_task_reminders(
        db,
        task,
        REMINDER_PRESETS[preset]
    )

    return task


def get_task_reminders(
    db: Session,
    task_id: int,
    telegram_id: int
) -> List[Reminder]:
    return (
        db.query(Reminder)
        .join(Task)
        .join(User)
        .filter(
            Reminder.task_id == task_id,
            User.telegram_id == telegram_id,
            Reminder.sent_at.is_(None)
        )
        .order_by(Reminder.remind_at.asc())
        .all()
    )


def get_due_reminders(
    db: Session
) -> List[Dict[str, Any]]:
    rows = (
        db.query(Reminder, Task, User.telegram_id)
        .join(Task, Reminder.task_id == Task.id)
        .join(User, Task.user_id == User.id)
        .filter(
            Task.status == "Pending",
            Reminder.sent_at.is_(None),
            Reminder.remind_at <= now_local()
        )
        .order_by(Reminder.remind_at.asc())
        .all()
    )

    return [
        {
            "reminder_id": reminder.id,
            "task_id": task.id,
            "telegram_id": telegram_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "deadline": task.deadline,
            "offset_minutes": reminder.offset_minutes,
        }
        for reminder, task, telegram_id in rows
    ]


def mark_reminder_as_sent(
    db: Session,
    reminder_id: int,
    telegram_message_id: int
) -> None:
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id)
        .first()
    )

    if reminder is None:
        return

    reminder.sent_at = now_local()
    reminder.telegram_message_id = telegram_message_id
    db.commit()


def remove_pending_reminders(
    db: Session,
    task_id: int
) -> None:
    (
        db.query(Reminder)
        .filter(
            Reminder.task_id == task_id,
            Reminder.sent_at.is_(None)
        )
        .delete(synchronize_session=False)
    )
    db.commit()


def remove_all_task_reminders(
    db: Session,
    task_id: int
) -> None:
    (
        db.query(Reminder)
        .filter(Reminder.task_id == task_id)
        .delete(synchronize_session=False)
    )
    db.commit()


def backfill_missing_reminders(db: Session) -> None:
    tasks = (
        db.query(Task)
        .filter(Task.status == "Pending")
        .all()
    )

    for task in tasks:
        reminder_count = (
            db.query(Reminder)
            .filter(Reminder.task_id == task.id)
            .count()
        )

        if reminder_count == 0:
            create_reminders_for_task(db, task)
