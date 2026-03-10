import logging
from aiogram import executor

import handlers
from loader import db, dp


async def on_startup(dispatcher):
    logging.basicConfig(level=logging.INFO)

    await db.connect()
    await db.setup()

    logging.info("Database connected")
    logging.info("Bot started")


async def on_shutdown(dispatcher):
    logging.info("Shutting down bot...")

    await db.close()

    logging.info("Database closed")
    logging.info("Bot stopped")


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )