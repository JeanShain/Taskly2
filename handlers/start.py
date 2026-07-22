from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from config import TIMEZONE, START_PHOTO_ID
from database import SessionLocal
from keyboards.main_menu import (back_to_main_keyboard, main_menu_keyboard,)
from services.task_service import get_statistics
from services.ui_service import (delete_message_safely, remove_legacy_reply_keyboard, render_screen, render_home_photo)
from services.user_service import get_or_create_user
from pathlib import Path
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, Message

router = Router()

@router.message(F.photo)
async def get_photo_file_id(message: Message):
    if not message.photo:
        return

    photo = message.photo[-1]

    print(f"START_PHOTO_ID={photo.file_id}")

    await message.answer(
        f"START_PHOTO_ID={photo.file_id}"
    )


def build_home_text(
    first_name: str,
    telegram_id: int
) -> str:
    db = SessionLocal()

    try:
        stats = get_statistics(db, telegram_id)
    finally:
        db.close()

    return (

        f"👋 Вітаю, {first_name}!\n\n"
        "Мене звуть Taskly, я твій особистий менеджер по денних питаннях!\n\n"
        f"Активних завдань: {stats['pending']}\n"
        f"Виконаних: {stats['completed']}\n"
        f"Прострочених: {stats['overdue']}\n\n"
        "Оберіть потрібну дію:"
    )


async def show_home(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    first_name: str
) -> None:
    caption = build_home_text(
        first_name=first_name,
        telegram_id=telegram_id
    )

    await render_home_photo(
        bot=bot,
        chat_id=chat_id,
        telegram_id=telegram_id,
        photo_id=START_PHOTO_ID,
        caption=caption,
        reply_markup=main_menu_keyboard()
    )


@router.message(CommandStart())
async def start_handler(
    message: Message,
    bot: Bot,
    state: FSMContext,
):
    telegram_user = message.from_user

    if telegram_user is None:
        return

    await state.clear()

    db = SessionLocal()
    try:
        get_or_create_user(
            db=db,
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )
    finally:
        db.close()

    await delete_message_safely(message)
    await remove_legacy_reply_keyboard(bot, message.chat.id)

    await show_home(
        bot=bot,
        chat_id=message.chat.id,
        telegram_id=telegram_user.id,
        first_name=telegram_user.first_name,
    )


@router.callback_query(F.data == "menu:home")
async def home_callback(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()

    await show_home(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name
    )


@router.callback_query(F.data == "menu:help")
async def help_callback(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()

    await render_screen(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        text=(
            "✱ Як користуватися Taskly\n\n"
            "1. Створіть завдання.\n"
            "2. Введіть назву, опис і дедлайн.\n"
            "3. Оберіть пріоритет.\n"
            "4. Відкрийте завдання зі списку, щоб виконати, "
            "відредагувати або видалити його.\n\n"
            "⛑︎ ︎Під час введення Taskly2 видаляє ваші службові "
            "повідомлення, тому чат залишається чистим."
        ),
        reply_markup=back_to_main_keyboard()
    )


@router.callback_query(F.data == "menu:settings")
async def settings_callback(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()

    await render_screen(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        text=(
            "⚒︎ Налаштування Taskly\n\n"
            f"Часовий пояс: {TIMEZONE}\n"
            "Нагадування: у момент настання дедлайну\n"
            "Мова інтерфейсу: українська\n"
            "Режим інтерфейсу: чистий чат"
        ),
        reply_markup=back_to_main_keyboard()
    )
