from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from database import SessionLocal
from keyboards.main_menu import back_to_main_keyboard
from keyboards.task_keyboard import (
    reminder_settings_keyboard,
    task_actions_keyboard,
)
from services.reminder_service import (
    REMINDER_PRESET_NAMES,
    get_task_reminders,
    set_task_reminder_preset,
)
from services.task_service import (
    complete_task,
    get_task_for_user,
)
from services.ui_service import render_screen
from utils.helpers import format_deadline, format_task


router = Router()


async def render_reminder_settings(
    bot: Bot,
    telegram_id: int,
    task_id: int
) -> None:
    db = SessionLocal()

    try:
        task = get_task_for_user(
            db,
            task_id,
            telegram_id
        )

        if task is None:
            reminders = []
        else:
            reminders = get_task_reminders(
                db,
                task_id,
                telegram_id
            )
    finally:
        db.close()

    if task is None:
        await render_screen(
            bot,
            telegram_id,
            telegram_id,
            "Завдання не знайдено :(",
            back_to_main_keyboard()
        )
        return

    preset_name = REMINDER_PRESET_NAMES.get(
        task.reminder_preset,
        task.reminder_preset
    )

    lines = [
        "⚠︎ Нагадування",
        "",
        f"Завдання: {task.title}",
        f"Поточний режим: {preset_name}",
        "",
    ]

    if reminders:
        lines.append("Майбутні сповіщення:")

        for reminder in reminders:
            lines.append(
                f"• {format_deadline(reminder.remind_at)}"
            )
    else:
        lines.append("Майбутніх сповіщень немає.")

    lines.extend(
        [
            "",
            "Оберіть новий режим:"
        ]
    )

    await render_screen(
        bot,
        telegram_id,
        telegram_id,
        "\n".join(lines),
        reminder_settings_keyboard(task_id)
    )


@router.callback_query(F.data.startswith("reminder:menu:"))
async def reminder_menu_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_task_id(callback.data)
    await callback.answer()

    await render_reminder_settings(
        bot,
        callback.from_user.id,
        task_id
    )


@router.callback_query(F.data.startswith("reminder:set:"))
async def reminder_set_callback(
    callback: CallbackQuery,
    bot: Bot
):
    parts = (callback.data or "").split(":")

    if len(parts) != 4 or not parts[2].isdigit():
        await callback.answer(
            "Некоректні дані",
            show_alert=True
        )
        return

    task_id = int(parts[2])
    preset = parts[3]

    db = SessionLocal()

    try:
        task = set_task_reminder_preset(
            db=db,
            task_id=task_id,
            telegram_id=callback.from_user.id,
            preset=preset
        )
    finally:
        db.close()

    if task is None:
        await callback.answer(
            "Не вдалося змінити нагадування",
            show_alert=True
        )
        return

    await callback.answer("Нагадування оновлено")

    await render_reminder_settings(
        bot,
        callback.from_user.id,
        task_id
    )


@router.callback_query(F.data.startswith("notice:seen:"))
async def reminder_seen_callback(
    callback: CallbackQuery
):
    await callback.answer("Нагадування прибрано")

    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass


@router.callback_query(F.data.startswith("notice:complete:"))
async def reminder_complete_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_task_id(callback.data)
    db = SessionLocal()

    try:
        task = complete_task(
            db=db,
            task_id=task_id,
            telegram_id=callback.from_user.id
        )
    finally:
        db.close()

    if task is None:
        await callback.answer(
            "Завдання не знайдено",
            show_alert=True
        )
        return

    await callback.answer("Завдання виконано")

    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "✅ Завдання виконано!\n\n"
        f"{format_task(task)}",
        task_actions_keyboard(task.id, task.status)
    )


def parse_task_id(callback_data: str) -> int:
    try:
        return int(callback_data.split(":")[-1])
    except (AttributeError, ValueError):
        return 0
