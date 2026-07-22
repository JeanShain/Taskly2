from pathlib import Path
from typing import Optional, Union

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
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

PhotoSource = Union[str, Path]


def prepare_photo_source(
    photo_source: PhotoSource,
):
    """
    Підтримує два варіанти:

    1. Telegram file_id як рядок.
    2. Локальний файл через Path або рядок-шлях.
    """

    if isinstance(photo_source, Path):
        if not photo_source.is_file():
            return None

        return FSInputFile(photo_source)

    if isinstance(photo_source, str):
        photo_source = photo_source.strip()

        if not photo_source:
            return None

        # Перевіряємо, чи рядок є шляхом до локального файла.
        possible_path = Path(photo_source)

        if possible_path.is_file():
            return FSInputFile(possible_path)

        # Інакше вважаємо його Telegram file_id.
        return photo_source

    return None


async def render_photo_screen(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    photo_path: PhotoSource,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Optional[int]:
    """
    Показує екран у вигляді:

    фотографія + підпис + Inline-кнопки.

    Працює як із локальними файлами,
    так і з Telegram file_id.
    """

    photo = prepare_photo_source(photo_path)

    if photo is None:
        print(
            "Зображення не знайдено або file_id не вказаний:",
            photo_path,
        )

        return await render_screen(
            bot=bot,
            chat_id=chat_id,
            telegram_id=telegram_id,
            text=caption,
            reply_markup=reply_markup,
        )

    db = SessionLocal()

    try:
        message_id = get_interface_message_id(
            db=db,
            telegram_id=telegram_id,
        )
    finally:
        db.close()

    if message_id is not None:
        try:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(
                    media=photo,
                    caption=caption,
                    parse_mode="HTML",
                ),
                reply_markup=reply_markup,
            )

            return message_id

        except TelegramBadRequest as error:
            error_text = str(error).lower()

            if "message is not modified" in error_text:
                return message_id

            print(
                "Не вдалося відредагувати медіаповідомлення:",
                error,
            )

            try:
                await bot.delete_message(
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except (
                TelegramBadRequest,
                TelegramForbiddenError,
            ):
                pass

        except TelegramForbiddenError:
            return None

    try:
        sent_message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    except TelegramBadRequest as error:
        print(
            "Telegram не прийняв зображення або file_id:",
            error,
        )

        return await render_screen(
            bot=bot,
            chat_id=chat_id,
            telegram_id=telegram_id,
            text=caption,
            reply_markup=reply_markup,
        )

    except TelegramForbiddenError:
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
            text="⌨",
            reply_markup=ReplyKeyboardRemove(),
        )
    except (TelegramBadRequest, TelegramForbiddenError):
        pass