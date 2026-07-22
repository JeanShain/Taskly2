import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import REMINDER_CHECK_SECONDS, TIMEZONE
from database import SessionLocal
from keyboards.task_keyboard import (
    reminder_notification_keyboard,
)
from services.reminder_service import (
    backfill_missing_reminders,
    get_due_reminders,
    mark_reminder_as_sent,
    reminder_offset_to_text,
)
from utils.helpers import format_deadline, priority_to_text


logger = logging.getLogger(__name__)


async def check_and_send_reminders(bot: Bot):
    db = SessionLocal()

    try:
        reminders = get_due_reminders(db)

        for reminder in reminders:
            try:
                sent_message = await bot.send_message(
                    chat_id=reminder["telegram_id"],
                    text=(
                        "🔔 Нагадування Taskly\n\n"
                        f"{reminder_offset_to_text(reminder['offset_minutes'])}\n\n"
                        f"◻︎ Назва: {reminder['title']}\n"
                        f"⏲︎ Дедлайн: "
                        f"{format_deadline(reminder['deadline'])}\n"
                        f"★ Пріоритет: "
                        f"{priority_to_text(reminder['priority'])}"
                    ),
                    reply_markup=reminder_notification_keyboard(
                        reminder_id=reminder["reminder_id"],
                        task_id=reminder["task_id"]
                    )
                )

                mark_reminder_as_sent(
                    db=db,
                    reminder_id=reminder["reminder_id"],
                    telegram_message_id=sent_message.message_id
                )
            except Exception:
                logger.exception(
                    "Не вдалося надіслати нагадування reminder_id=%s",
                    reminder["reminder_id"]
                )
    finally:
        db.close()


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    db = SessionLocal()

    try:
        backfill_missing_reminders(db)
    finally:
        db.close()

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        seconds=REMINDER_CHECK_SECONDS,
        args=[bot],
        id="taskly_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    scheduler.start()
    return scheduler
