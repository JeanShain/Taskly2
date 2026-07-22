from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from config import CALENDAR_EVENT_MINUTES, TIMEZONE
from models.task import Task
from services.time_service import attach_timezone


def escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def event_times(task: Task):
    deadline = attach_timezone(task.deadline)
    start = deadline - timedelta(minutes=CALENDAR_EVENT_MINUTES)
    end = deadline
    return start, end


def generate_ics(task: Task) -> bytes:
    start, end = event_times(task)
    created_utc = datetime.now(timezone.utc)

    title = escape_ics_text(f"Taskly: {task.title}")
    description = escape_ics_text(
        task.description or "Особисте завдання у Taskly"
    )

    content = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Taskly//Telegram Task Manager//UK",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:taskly-task-{task.id}@taskly.local",
            f"DTSTAMP:{created_utc.strftime('%Y%m%dT%H%M%SZ')}",
            (
                f"DTSTART;TZID={TIMEZONE}:"
                f"{start.strftime('%Y%m%dT%H%M%S')}"
            ),
            (
                f"DTEND;TZID={TIMEZONE}:"
                f"{end.strftime('%Y%m%dT%H%M%S')}"
            ),
            f"SUMMARY:{title}",
            f"DESCRIPTION:{description}",
            "BEGIN:VALARM",
            "TRIGGER:-PT10M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Нагадування Taskly",
            "END:VALARM",
            "END:VEVENT",
            "END:VCALENDAR",
            ""
        ]
    )

    return content.encode("utf-8")


def build_google_calendar_url(task: Task) -> str:
    start, end = event_times(task)
    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)

    params = {
        "action": "TEMPLATE",
        "text": f"Taskly: {task.title}",
        "dates": (
            f"{start_utc.strftime('%Y%m%dT%H%M%SZ')}/"
            f"{end_utc.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        "details": (
            task.description
            or "Особисте завдання, створене у Taskly."
        ),
        "ctz": TIMEZONE,
    }

    return (
        "https://calendar.google.com/calendar/render?"
        + urlencode(params)
    )
