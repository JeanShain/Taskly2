from aiogram import Bot, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from handlers.start import show_home
from services.ui_service import delete_message_safely


router = Router()



@router.message(StateFilter(None))
async def fallback_message(message: Message, bot: Bot):
    if message.from_user is None:
        return

    await delete_message_safely(message)

    await show_home(
        bot=bot,
        chat_id=message.chat.id,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
    )