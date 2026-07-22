from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from database import SessionLocal
from keyboards.main_menu import back_to_main_keyboard
from services.task_service import get_statistics
from services.screen_images import STATISTICS_IMAGE
from services.ui_service import render_photo_screen


router = Router()


@router.callback_query(F.data == "menu:stats")
async def statistics_callback(
    callback: CallbackQuery,
    bot: Bot
):
    db = SessionLocal()

    try:
        stats = get_statistics(
            db=db,
            telegram_id=callback.from_user.id
        )
    finally:
        db.close()

    await callback.answer()

    await render_photo_screen(
        bot=bot,
        chat_id=callback.from_user.id,
        telegram_id=callback.from_user.id,
        photo_path=STATISTICS_IMAGE,
        caption=(
            "✱ Ваша статистика\n\n"
            f"Усього створено: {stats['total']}\n"
            f"Активних: {stats['pending']}\n"
            f"Виконаних: {stats['completed']}\n"
            f"Прострочених: {stats['overdue']}\n"
            f"Результативність: {stats['completion_rate']}%"
        ),
        reply_markup=back_to_main_keyboard(),
    )
