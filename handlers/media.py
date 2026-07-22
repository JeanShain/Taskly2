from aiogram import F, Router
from aiogram.types import Message


router = Router()


@router.message(F.photo)
async def get_photo_file_id(message: Message):
    if not message.photo:
        return

    # Telegram надсилає кілька розмірів фотографії.
    # Останній елемент зазвичай має найбільшу якість.
    file_id = message.photo[-1].file_id

    print(f"PHOTO_FILE_ID={file_id}")

    await message.answer(
        "ID фотографії:\n\n"
        f"<code>{file_id}</code>",
        parse_mode="HTML"
    )


@router.message(F.animation)
async def get_animation_file_id(message: Message):
    if message.animation is None:
        return

    file_id = message.animation.file_id

    print(f"ANIMATION_FILE_ID={file_id}")

    await message.answer(
        "ID анімації:\n\n"
        f"<code>{file_id}</code>",
        parse_mode="HTML"
    )


@router.message(F.document)
async def get_document_file_id(message: Message):
    if message.document is None:
        return

    mime_type = message.document.mime_type or ""

    # Обробляємо лише зображення, надіслані як файл.
    if not mime_type.startswith("image/"):
        return

    file_id = message.document.file_id

    print(f"DOCUMENT_IMAGE_FILE_ID={file_id}")

    await message.answer(
        "ID зображення, надісланого як файл:\n\n"
        f"<code>{file_id}</code>",
        parse_mode="HTML"
    )