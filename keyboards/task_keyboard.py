from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.task import Task


def priority_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🙂 Низький",
                    callback_data="create:priority:Low"
                )
            ],
            [
                InlineKeyboardButton(
                    text="😐 Середній",
                    callback_data="create:priority:Medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🙁 Високий",
                    callback_data="create:priority:High"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✘ Скасувати",
                    callback_data="flow:cancel"
                )
            ]
        ]
    )


def cancel_flow_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✘ Скасувати",
                    callback_data="flow:cancel"
                )
            ]
        ]
    )


def task_list_keyboard(
    tasks: List[Task],
    back_callback: str = "menu:home"
) -> InlineKeyboardMarkup:
    rows = []

    for task in tasks:
        title = task.title

        if len(title) > 34:
            title = title[:31] + "…"

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"◻︎ {title}",
                    callback_data=f"task:view:{task.id}"
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="← Назад",
                callback_data=back_callback
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_actions_keyboard(
    task_id: int,
    status: str
) -> InlineKeyboardMarkup:
    rows = []

    if status != "Completed":
        rows.append(
            [
                InlineKeyboardButton(
                    text="✔ Виконати",
                    callback_data=f"task:complete:{task_id}"
                )
            ]
        )

    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="✏️ Редагувати",
                    callback_data=f"task:edit:{task_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Видалити",
                    callback_data=f"task:delete:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔔 Нагадування",
                    callback_data=f"reminder:menu:{task_id}"
                ),
                InlineKeyboardButton(
                    text="🔎 Джерела",
                    callback_data=f"task:sources:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Календар",
                    callback_data=f"task:calendar:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← До списку",
                    callback_data="menu:tasks"
                ),
                InlineKeyboardButton(
                    text="⌂ Меню",
                    callback_data="menu:home"
                )
            ]
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Так, видалити",
                    callback_data=f"task:delete_confirm:{task_id}"
                ),
                InlineKeyboardButton(
                    text="Ні",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def edit_fields_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назва",
                    callback_data=f"edit:title:{task_id}"
                ),
                InlineKeyboardButton(
                    text="Опис",
                    callback_data=f"edit:description:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Дедлайн",
                    callback_data=f"edit:deadline:{task_id}"
                ),
                InlineKeyboardButton(
                    text="Пріоритет",
                    callback_data=f"edit:priority_menu:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def edit_priority_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🙂 Низький",
                    callback_data=f"edit:priority:{task_id}:Low"
                )
            ],
            [
                InlineKeyboardButton(
                    text="😐 Середній",
                    callback_data=f"edit:priority:{task_id}:Medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🙁 Високий",
                    callback_data=f"edit:priority:{task_id}:High"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data=f"task:edit:{task_id}"
                )
            ]
        ]
    )


def reminder_settings_keyboard(
    task_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 день + 1 год. + дедлайн",
                    callback_data=(
                        f"reminder:set:{task_id}:default"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="1 год. + дедлайн",
                    callback_data=f"reminder:set:{task_id}:hour"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Лише дедлайн",
                    callback_data=(
                        f"reminder:set:{task_id}:deadline"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="Без нагадувань",
                    callback_data=f"reminder:set:{task_id}:none"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← До завдання",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def reminder_notification_keyboard(
    reminder_id: int,
    task_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Виконано",
                    callback_data=f"notice:complete:{task_id}"
                ),
                InlineKeyboardButton(
                    text="👁 Побачив",
                    callback_data=f"notice:seen:{reminder_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Відкрити завдання",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def source_results_keyboard(
    task_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Оновити джерела",
                    callback_data=f"task:sources:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← До завдання",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def calendar_keyboard(
    task_id: int,
    google_calendar_url: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Завантажити .ics",
                    callback_data=f"calendar:ics:{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Google Calendar",
                    url=google_calendar_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="← До завдання",
                    callback_data=f"task:view:{task_id}"
                )
            ]
        ]
    )


def export_cleanup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧹 Прибрати файл із чату",
                    callback_data="export:delete"
                )
            ]
        ]
    )
