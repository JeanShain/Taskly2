from datetime import datetime
from zoneinfo import ZoneInfo

from config import TIMEZONE


def timezone_info() -> ZoneInfo:
    return ZoneInfo(TIMEZONE)


def now_local() -> datetime:

    # nовертає локальний час для сумісності з SQLite
    return datetime.now(timezone_info()).replace(tzinfo=None)


def attach_timezone(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone_info())

    return value.replace(tzinfo=timezone_info())
