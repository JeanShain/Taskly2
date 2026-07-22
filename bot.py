import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, validate_config
from database import init_db
from handlers.fallback import router as fallback_router
from handlers.integrations import router as integrations_router
from handlers.reminders import router as reminders_router
from handlers.start import router as start_router
from handlers.statistics import router as statistics_router
from handlers.tasks import router as tasks_router
from scheduler import start_scheduler


async def main():
    validate_config()
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(tasks_router)
    dp.include_router(reminders_router)
    dp.include_router(integrations_router)
    dp.include_router(statistics_router)
    dp.include_router(fallback_router)

    scheduler = start_scheduler(bot)

    logging.info("Taskly2 is running...")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Taskly stopped.")
