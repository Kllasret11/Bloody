import logging
from aiogram import executor

from loader import dp, db, bot
import handlers


logging.basicConfig(level=logging.INFO)


async def on_startup(dispatcher):
    await db.connect()
    await db.setup()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    print("✅ Bot started")


async def on_shutdown(dispatcher):
    await db.close()
    print("🛑 Bot stopped")


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
