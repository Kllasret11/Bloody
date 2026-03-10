import logging
<<<<<<< HEAD
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
=======

from aiogram import executor

import handlers  # noqa: F401
from loader import db, dp


async def on_startup(_: object) -> None:
    logging.basicConfig(level=logging.INFO)
    await db.connect()
    await db.setup()
    logging.info("Bot started")


async def on_shutdown(_: object) -> None:
    await db.close()
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
    logging.info("Bot stopped")


if __name__ == "__main__":
<<<<<<< HEAD
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
=======
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
