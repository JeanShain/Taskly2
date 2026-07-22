from datetime import datetime
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import SessionLocal
from handlers.start import show_home
from keyboards.main_menu import back_to_main_keyboard
from keyboards.task_keyboard import (
    cancel_flow_keyboard,
    confirm_delete_keyboard,
    edit_fields_keyboard,
    edit_priority_keyboard,
    priority_keyboard,
    task_actions_keyboard,
    task_list_keyboard,
)
from services.source_service import is_research_task
from services.task_service import (
    complete_task,
    create_task,
    delete_task,
    get_task_for_user,
    get_tasks_for_user,
    get_today_tasks,
    update_task,
)
from services.ui_service import (
    delete_message_safely,
    render_screen,
)
from services.user_service import get_user_by_telegram_id
from utils.helpers import format_task, parse_deadline


router = Router()


class CreateTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_priority = State()


class EditTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@router.callback_query(F.data == "menu:create")
async def start_task_creation(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    await state.clear()
    await state.set_state(CreateTaskStates.waiting_for_title)
    await callback.answer()

    await render_screen(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        text=(
            "✱ Створення завдання\n\n"
            "Введіть назву завдання.\n\n"
            "⛑︎ Наприклад: звіт за сьогодні"
        ),
        reply_markup=cancel_flow_keyboard()
    )


@router.message(CreateTaskStates.waiting_for_title)
async def process_task_title(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    title = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    if len(title) < 3:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Назва занадто коротка.\n\n"
            "⛑︎ Введіть щонайменше 3 символи:",
            cancel_flow_keyboard()
        )
        return

    if len(title) > 255:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Назва занадто довга.\n\n"
            "⛑︎ Максимум — 255 символів:",
            cancel_flow_keyboard()
        )
        return

    await state.update_data(title=title)
    await state.set_state(CreateTaskStates.waiting_for_description)

    await render_screen(
        bot,
        message.chat.id,
        message.from_user.id,
        "✱ Створення завдання\n\n"
        f"Назва: {title}\n\n"
        "Додайте опис завдання.\n"
        "⛑︎ Щоб пропустити цей крок, надішліть символ: -",
        cancel_flow_keyboard()
    )


@router.message(CreateTaskStates.waiting_for_description)
async def process_task_description(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    description_text = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    if len(description_text) > 2000:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Опис занадто довгий.\n\n"
            "⛑︎ Максимум — 2000 символів:",
            cancel_flow_keyboard()
        )
        return

    description = None if description_text == "-" else description_text

    await state.update_data(description=description)
    await state.set_state(CreateTaskStates.waiting_for_deadline)

    await render_screen(
        bot,
        message.chat.id,
        message.from_user.id,
        "✱ Створення завдання\n\n"
        "Введіть дату і час виконання у форматі:\n\n"
        "ДД.ММ.РРРР ГГ:ХХ\n\n"
        "⛑︎ Наприклад: 25.07.2026 18:30",
        cancel_flow_keyboard()
    )


@router.message(CreateTaskStates.waiting_for_deadline)
async def process_task_deadline(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    deadline_text = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    try:
        deadline = parse_deadline(deadline_text)
    except ValueError:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Неправильний формат дати.\n\n"
            "⛑︎ Введіть дату так: 25.07.2026 18:30",
            cancel_flow_keyboard()
        )
        return

    from services.time_service import now_local

    if deadline <= now_local():
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Дедлайн має бути в майбутньому.\n\n"
            "Введіть іншу дату:",
            cancel_flow_keyboard()
        )
        return

    await state.update_data(
        deadline=deadline.strftime("%Y-%m-%d %H:%M:%S")
    )
    await state.set_state(CreateTaskStates.waiting_for_priority)

    await render_screen(
        bot,
        message.chat.id,
        message.from_user.id,
        "✱ Створення завдання\n\n"
        "Оберіть пріоритет:",
        priority_keyboard()
    )


@router.callback_query(
    CreateTaskStates.waiting_for_priority,
    F.data.startswith("create:priority:")
)
async def process_task_priority(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    priority = (callback.data or "").split(":")[-1]

    if priority not in {"Low", "Medium", "High"}:
        await callback.answer(
            "Невідомий пріоритет",
            show_alert=True
        )
        return

    task_data = await state.get_data()
    deadline = datetime.strptime(
        task_data["deadline"],
        "%Y-%m-%d %H:%M:%S"
    )

    db = SessionLocal()

    try:
        user = get_user_by_telegram_id(
            db,
            callback.from_user.id
        )

        if user is None:
            await callback.answer(
                "Спочатку надішліть /start",
                show_alert=True
            )
            await state.clear()
            return

        task = create_task(
            db=db,
            user_id=user.id,
            title=task_data["title"],
            description=task_data.get("description"),
            priority=priority,
            deadline=deadline
        )
    finally:
        db.close()

    await state.clear()
    await callback.answer("Завдання створено")

    prefix = "✔ Завдання успішно створено!\n\n"

    if is_research_task(task.title, task.description):
        prefix += (
            "𓁶 Схоже на навчальне або дослідницьке завдання. "
            "Кнопка «🔎 Джерела» підбере матеріали.\n\n"
        )

    await render_task_detail(
        bot=bot,
        telegram_id=callback.from_user.id,
        task_id=task.id,
        prefix=prefix
    )


@router.callback_query(F.data == "flow:cancel")
async def cancel_flow(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()
    edit_task_id = data.get("edit_task_id")

    await state.clear()
    await callback.answer("Дію скасовано")

    if edit_task_id:
        await render_task_detail(
            bot,
            callback.from_user.id,
            int(edit_task_id)
        )
        return

    await show_home(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name
    )


@router.callback_query(F.data == "menu:tasks")
async def show_all_tasks(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()
    await render_task_list(
        bot=bot,
        telegram_id=callback.from_user.id,
        today_only=False
    )


@router.callback_query(F.data == "menu:today")
async def show_today_tasks(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()
    await render_task_list(
        bot=bot,
        telegram_id=callback.from_user.id,
        today_only=True
    )


async def render_task_list(
    bot: Bot,
    telegram_id: int,
    today_only: bool
) -> None:
    db = SessionLocal()

    try:
        if today_only:
            tasks = get_today_tasks(db, telegram_id)
            title = "📅 Завдання на сьогодні"
        else:
            tasks = get_tasks_for_user(db, telegram_id)
            title = "📋 Мої активні завдання"
    finally:
        db.close()

    if not tasks:
        await render_screen(
            bot,
            telegram_id,
            telegram_id,
            f"{title}\n\nАктивних завдань не знайдено.",
            back_to_main_keyboard()
        )
        return

    lines = [title, ""]

    for number, task in enumerate(tasks, start=1):
        lines.append(
            f"{number}. {task.title} — "
            f"{task.deadline.strftime('%d.%m %H:%M')}"
        )

    lines.append("")
    lines.append("Оберіть завдання:")

    await render_screen(
        bot,
        telegram_id,
        telegram_id,
        "\n".join(lines),
        task_list_keyboard(tasks)
    )


@router.callback_query(F.data.startswith("task:view:"))
async def view_task(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await callback.answer()

    await render_task_detail(
        bot,
        callback.from_user.id,
        task_id
    )


async def render_task_detail(
    bot: Bot,
    telegram_id: int,
    task_id: int,
    prefix: str = ""
) -> None:
    db = SessionLocal()

    try:
        task = get_task_for_user(
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
            "Завдання не знайдено.",
            back_to_main_keyboard()
        )
        return

    await render_screen(
        bot,
        telegram_id,
        telegram_id,
        f"{prefix}{format_task(task)}",
        task_actions_keyboard(task.id, task.status)
    )


@router.callback_query(F.data.startswith("task:complete:"))
async def complete_task_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    db = SessionLocal()

    try:
        task = complete_task(
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

    await callback.answer("Завдання виконано")
    await render_task_detail(
        bot,
        callback.from_user.id,
        task.id,
        prefix="✔ Виконано!\n\n"
    )


@router.callback_query(F.data.startswith("task:delete:"))
async def ask_delete_confirmation(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "🗑 Видалити це завдання?\n\n"
        "⛑︎ Цю дію неможливо скасувати.",
        confirm_delete_keyboard(task_id)
    )


@router.callback_query(
    F.data.startswith("task:delete_confirm:")
)
async def confirm_delete_callback(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    db = SessionLocal()

    try:
        deleted = delete_task(
            db,
            task_id,
            callback.from_user.id
        )
    finally:
        db.close()

    if not deleted:
        await callback.answer(
            "Завдання не знайдено :(",
            show_alert=True
        )
        return

    await callback.answer("Завдання видалено")
    await render_task_list(
        bot,
        callback.from_user.id,
        today_only=False
    )


@router.callback_query(F.data.startswith("task:edit:"))
async def open_edit_menu(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "✏️ Що потрібно змінити?",
        edit_fields_keyboard(task_id)
    )


@router.callback_query(F.data.startswith("edit:title:"))
async def start_title_edit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await state.set_state(EditTaskStates.waiting_for_title)
    await state.update_data(edit_task_id=task_id)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "Введіть нову назву завдання:",
        cancel_flow_keyboard()
    )


@router.message(EditTaskStates.waiting_for_title)
async def process_title_edit(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    title = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    if not 3 <= len(title) <= 255:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "⛑︎ Назва повинна містити від 3 до 255 символів:",
            cancel_flow_keyboard()
        )
        return

    data = await state.get_data()
    task = perform_task_update(
        message.from_user.id,
        data["edit_task_id"],
        title=title
    )

    await state.clear()
    await finish_edit(bot, message.from_user.id, task)


@router.callback_query(
    F.data.startswith("edit:description:")
)
async def start_description_edit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await state.set_state(
        EditTaskStates.waiting_for_description
    )
    await state.update_data(edit_task_id=task_id)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "Введіть новий опис.\n"
        "⛑︎ Надішліть «-», щоб прибрати опис:",
        cancel_flow_keyboard()
    )


@router.message(EditTaskStates.waiting_for_description)
async def process_description_edit(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    description_text = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    if len(description_text) > 2000:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Опис занадто довгий.\n"
            "⛑︎ Максимум — 2000 символів:",
            cancel_flow_keyboard()
        )
        return

    description = (
        None
        if description_text == "-"
        else description_text
    )
    data = await state.get_data()

    task = perform_task_update(
        message.from_user.id,
        data["edit_task_id"],
        description=description
    )

    await state.clear()
    await finish_edit(bot, message.from_user.id, task)


@router.callback_query(F.data.startswith("edit:deadline:"))
async def start_deadline_edit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await state.set_state(EditTaskStates.waiting_for_deadline)
    await state.update_data(edit_task_id=task_id)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "Введіть новий дедлайн:\n\n"
        "ДД.ММ.РРРР ГГ:ХХ",
        cancel_flow_keyboard()
    )


@router.message(EditTaskStates.waiting_for_deadline)
async def process_deadline_edit(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    deadline_text = message.text.strip() if message.text else ""
    await delete_message_safely(message)

    try:
        deadline = parse_deadline(deadline_text)
    except ValueError:
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "Неправильний формат.\n"
            "⛑︎ Наприклад: 25.07.2026 18:30",
            cancel_flow_keyboard()
        )
        return

    from services.time_service import now_local

    if deadline <= now_local():
        await render_screen(
            bot,
            message.chat.id,
            message.from_user.id,
            "⛑︎ Дедлайн має бути в майбутньому:",
            cancel_flow_keyboard()
        )
        return

    data = await state.get_data()
    task = perform_task_update(
        message.from_user.id,
        data["edit_task_id"],
        deadline=deadline
    )

    await state.clear()
    await finish_edit(bot, message.from_user.id, task)


@router.callback_query(
    F.data.startswith("edit:priority_menu:")
)
async def open_priority_edit(
    callback: CallbackQuery,
    bot: Bot
):
    task_id = parse_last_int(callback.data)
    await callback.answer()

    await render_screen(
        bot,
        callback.from_user.id,
        callback.from_user.id,
        "Оберіть новий пріоритет:",
        edit_priority_keyboard(task_id)
    )


@router.callback_query(F.data.startswith("edit:priority:"))
async def process_priority_edit(
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
    priority = parts[3]

    if priority not in {"Low", "Medium", "High"}:
        await callback.answer(
            "Невідомий пріоритет",
            show_alert=True
        )
        return

    task = perform_task_update(
        callback.from_user.id,
        task_id,
        priority=priority
    )

    if task is None:
        await callback.answer(
            "Завдання не знайдено :(",
            show_alert=True
        )
        return

    await callback.answer("Пріоритет змінено")
    await render_task_detail(
        bot,
        callback.from_user.id,
        task.id,
        prefix="✔ Завдання оновлено!\n\n"
    )


def perform_task_update(
    telegram_id: int,
    task_id: int,
    **changes
):
    db = SessionLocal()

    try:
        return update_task(
            db=db,
            task_id=int(task_id),
            telegram_id=telegram_id,
            **changes
        )
    finally:
        db.close()


async def finish_edit(
    bot: Bot,
    telegram_id: int,
    task
) -> None:
    if task is None:
        await render_screen(
            bot,
            telegram_id,
            telegram_id,
            "Завдання не знайдено :(",
            back_to_main_keyboard()
        )
        return

    await render_task_detail(
        bot,
        telegram_id,
        task.id,
        prefix="✔ Завдання оновлено!\n\n"
    )


def parse_last_int(
    callback_data: Optional[str]
) -> int:
    try:
        return int((callback_data or "").split(":")[-1])
    except ValueError:
        return 0
