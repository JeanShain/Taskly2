from datetime import datetime

from models.task import Task


PRIORITY_NAMES = {
    "Low": "🙂 Низький",
    "Medium": "😐 Середній",
    "High": "🙁 Високий",
}

STATUS_NAMES = {
    "Pending": "Активне",
    "Completed": "Виконано",
}


def parse_deadline(value: str) -> datetime:
    return datetime.strptime(value, "%d.%m.%Y %H:%M")


def format_deadline(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M")


def priority_to_text(priority: str) -> str:
    return PRIORITY_NAMES.get(priority, priority)


def status_to_text(status: str) -> str:
    return STATUS_NAMES.get(status, status)


def format_task(task: Task) -> str:
    description = task.description or "Без опису"

    return (
        f"◻︎ Назва: {task.title}\n"
        f"✎ Опис: {description}\n"
        f"⏲︎ Дедлайн: {format_deadline(task.deadline)}\n"
        f"★ Пріоритет: {priority_to_text(task.priority)}\n"
        f"Статус: {status_to_text(task.status)}"
    )
