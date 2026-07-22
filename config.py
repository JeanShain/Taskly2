import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db").strip()
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv").strip()

START_PHOTO_ID = os.getenv(
    "START_PHOTO_ID",
    ""
).strip()

REMINDER_CHECK_SECONDS = int(
    os.getenv("REMINDER_CHECK_SECONDS", "30")
)
DEFAULT_REMINDER_OFFSETS = os.getenv(
    "DEFAULT_REMINDER_OFFSETS",
    "1440,60,0"
).strip()

CALENDAR_EVENT_MINUTES = int(
    os.getenv("CALENDAR_EVENT_MINUTES", "30")
)

SOURCE_SEARCH_TIMEOUT = int(
    os.getenv("SOURCE_SEARCH_TIMEOUT", "15")
)
CROSSREF_MAILTO = os.getenv("CROSSREF_MAILTO", "").strip()

# ai, ale mojna i bez nei, takoj work)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5").strip()


def parse_default_reminder_offsets() -> List[int]:
    offsets = []

    for raw_value in DEFAULT_REMINDER_OFFSETS.split(","):
        raw_value = raw_value.strip()

        if not raw_value:
            continue

        try:
            offset = int(raw_value)
        except ValueError as error:
            raise RuntimeError(
                "DEFAULT_REMINDER_OFFSETS повинен містити "
                "цілі числа через кому."
            ) from error

        if offset < 0:
            raise RuntimeError(
                "Значення нагадування не може бути від'ємним."
            )

        offsets.append(offset)

    return sorted(set(offsets), reverse=True)


def validate_config():
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не налаштований. Створіть бота через @BotFather "
            "і вставте отриманий токен у файл .env."
        )

    if REMINDER_CHECK_SECONDS < 10:
        raise RuntimeError(
            "REMINDER_CHECK_SECONDS має бути не менше 10 секунд."
        )

    if CALENDAR_EVENT_MINUTES < 5:
        raise RuntimeError(
            "CALENDAR_EVENT_MINUTES має бути не менше 5 хвилин."
        )

    parse_default_reminder_offsets()
