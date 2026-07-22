from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import (
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from database import SessionLocal
from services.user_service import (
    get_interface_message_id,
    set_interface_message_id,
)

async def render_home_photo(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    photo_id: str,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> Optional[int]:
    """
    Видаляє поточний екран Taskly та створює
    головне меню у вигляді GIF/анімації.
    """
    db = SessionLocal()

    try:
        old_message_id = get_interface_message_id(
            db=db,
            telegram_id=telegram_id
        )
    finally:
        db.close()

    # Прибираємо попередній текстовий або медіаекран
    if old_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=old_message_id
            )
        except (
            TelegramBadRequest,
            TelegramForbiddenError
        ):
            pass

    if not photo_id:
        return None

    try:
        sent_message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo_id,
            caption=caption,
            reply_markup=reply_markup
        )
    except (
        TelegramBadRequest,
        TelegramForbiddenError
    ):
        return None

    db = SessionLocal()

    try:
        set_interface_message_id(
            db=db,
            telegram_id=telegram_id,
            message_id=sent_message.message_id
        )
    finally:
        db.close()

    return sent_message.message_id


async def render_screen(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Optional[int]:
    """
    Видаляє попередній екран і створює новий текстовий екран.
    Працює однаково після фотографій і текстових повідомлень.
    """
    db = SessionLocal()
    try:
        old_message_id = get_interface_message_id(
            db=db,
            telegram_id=telegram_id,
        )
    finally:
        db.close()

    if old_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=old_message_id,
            )
        except (TelegramBadRequest, TelegramForbiddenError):
            pass

    try:
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )
    except (TelegramBadRequest, TelegramForbiddenError):
        return None

    db = SessionLocal()
    try:
        set_interface_message_id(
            db=db,
            telegram_id=telegram_id,
            message_id=sent_message.message_id,
        )
    finally:
        db.close()

    return sent_message.message_id

async def delete_message_safely(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    except TelegramForbiddenError:
        pass


async def remove_legacy_reply_keyboard(
    bot: Bot,
    chat_id: int,
) -> None:
    """
    Прибирає стару ReplyKeyboard.

    Повідомлення навмисно не видаляється одразу,
    щоб Telegram Desktop встиг застосувати ReplyKeyboardRemove.
    """
    try:
        await bot.send_message(
            chat_id=chat_id,
            text="⌨️ Поле введення оновлено. Тепер можна вводити текст.",
            reply_markup=ReplyKeyboardRemove(),
        )
    except (TelegramBadRequest, TelegramForbiddenError):
        pass