from aiogram import Bot, F, Router
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
)

from database import SessionLocal
from keyboards.main_menu import back_to_main_keyboard
from keyboards.task_keyboard import (
    calendar_keyboard,
    export_cleanup_keyboard,
    source_results_keyboard,
)
from services.calendar_service import (
    build_google_calendar_url,
    generate_ics,
)
from services.source_service import find_sources
from services.task_service import get_task_for_user
from services.ui_service import render_screen


router = Router()


@router.callback_query(F.data.startswith("task:sources:"))
async def sources_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_task_id(callback.data)
    db = SessionLocal()

    try:
        task = get_task_for_user(
            db,
            task_id,
            callback.from_user.id
        )
    finally:
        db.close()

    if task is None:
        await callback.answer(
            "Завдання не знайдено",
            show_alert=True
        )
        return

    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "🔎 шукаю реальні матеріали та джерела…\n\n"
        "⛑︎ це може тривати кілька секунд.",
        source_results_keyboard(task_id)
    )

    result = await find_sources(
        task_title=task.title,
        task_description=task.description
    )

    sources = result["sources"]
    ai_hint = result["ai_hint"]

    if not sources:
        text = (
            "🔎 Джерела\n\n"
            "Не вдалося отримати результати. "
            "⛑︎ Перевірте інтернет-з'єднання та спробуйте ще раз."
        )
    else:
        lines = [
            "⚲ Матеріали для завдання",
            f"«{task.title}»",
            "",
        ]

        for number, source in enumerate(sources, start=1):
            lines.extend(
                [
                    f"{number}. {source['title']}",
                    f"Тип: {source['kind']}",
                    source["summary"],
                    source["url"],
                    "",
                ]
            )

        if ai_hint:
            lines.extend(
                [
                    "𓁶 AI-підказка",
                    ai_hint,
                ]
            )
        else:
            lines.extend(
                [
                    "⛭ Підказка",
                    "Почніть із загального огляду теми, "
                    "після чого перевірте наукові джерела "
                    "та сформуйте 3–4 основні підрозділи.",
                ]
            )

        text = "\n".join(lines)

        # telegram має ліміт на довжину тексту повідомлення
        if len(text) > 3900:
            text = text[:3890].rstrip() + "…"

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        text,
        source_results_keyboard(task_id)
    )


@router.callback_query(F.data.startswith("task:calendar:"))
async def calendar_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_task_id(callback.data)
    db = SessionLocal()

    try:
        task = get_task_for_user(
            db,
            task_id,
            callback.from_user.id
        )
    finally:
        db.close()

    if task is None:
        await callback.answer(
            "Завдання не знайдено :(",
            show_alert=True
        )
        return

    await callback.answer()

    google_url = build_google_calendar_url(task)

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "📅Додавання в календар\n\n"
        f"Завдання: {task.title}\n"
        f"Дедлайн: {task.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
        "Файл .ics можна відкрити у календарі телефону "
        "або комп'ютера. Google Calendar відкриється "
        "з уже заповненими даними.",
        calendar_keyboard(task.id, google_url)
    )


@router.callback_query(F.data.startswith("calendar:ics:"))
async def calendar_ics_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_task_id(callback.data)
    db = SessionLocal()

    try:
        task = get_task_for_user(
            db,
            task_id,
            callback.from_user.id
        )
    finally:
        db.close()

    if task is None:
        await callback.answer(
            "Завдання не знайдено :(",
            show_alert=True
        )
        return

    ics_file = BufferedInputFile(
        generate_ics(task),
        filename=f"taskly_task_{task.id}.ics"
    )

    await bot.send_document(
        chat_id=callback.from_user.id,
        document=ics_file,
        caption=(
            "📅Відкрийте файл і підтвердьте "
            "додавання події до календаря."
        ),
        reply_markup=export_cleanup_keyboard()
    )

    await callback.answer("Файл календаря надіслано")


@router.callback_query(F.data == "export:delete")
async def delete_export_callback(
    callback: CallbackQuery
):
    await callback.answer("Файл прибрано")

    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass


def parse_task_id(callback_data: str) -> int:
    try:
        return int(callback_data.split(":")[-1])
    except (AttributeError, ValueError):
        return 0
