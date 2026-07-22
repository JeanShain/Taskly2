from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.photo)
async def get_photo_file_id(message: Message):
    if not message.photo:
        return

    file_id = message.photo[-1].file_id

    print(f"PHOTO_FILE_ID={file_id}")

    await message.answer(
        f"PHOTO_FILE_ID=\n{file_id}"
    )


@router.message(F.animation)
async def get_animation_file_id(message: Message):
    if message.animation is None:
        return

    file_id = message.animation.file_id

    print(f"ANIMATION_FILE_ID={file_id}")

    await message.answer(
        f"ANIMATION_FILE_ID=\n{file_id}"
    )