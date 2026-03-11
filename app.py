import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import executor

import handlers  # noqa: F401
from loader import bot, db, dp


async def on_startup(_: object) -> None:
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join("logs", "bot.log"),
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), file_handler],
    )
    await db.connect()
    await db.setup()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot started")


async def on_shutdown(_: object) -> None:
    await db.close()
    logging.info("Bot stopped")


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )