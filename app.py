import asyncio
import logging
import sys

from loader import dp, bot, db
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def send_notifications():
    due_payments = await db.get_due_payments_today()
    for payment in due_payments:
        info = (f"{payment[4]} mahsuloti uchun to'lov kuni keldi: {payment[5]}.\n"
               f"To'lov summasi: {payment[6]}$\n"
               f"Iltimos, to'lovni amalga oshiring.")
        await bot.send_message(payment[2], info)


async def on_startup():
    # Birlamchi komandalar (/star va /help)
    await set_default_commands()

    # Bot ishga tushgani haqida adminga xabar berish
    await on_startup_notify()
    scheduler.start()


async def main() -> None:
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_notifications, 'cron', hour=12, minute=33)
    asyncio.run(main())
