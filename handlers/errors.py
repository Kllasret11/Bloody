from __future__ import annotations

import logging

from aiogram import types

from loader import dp
from utils.notify_admins import format_exception, notify_admins


@dp.errors_handler()
async def global_error_handler(update: types.Update, exception: Exception):
    logging.exception("Unhandled exception: %s", exception)
    try:
        text = (
            "<b>🚨 Ошибка в боте</b>\n"
            f"Update: <code>{str(update)[:500]}</code>\n\n"
            f"<code>{format_exception(exception)}</code>"
        )
        await notify_admins(text)
    except Exception:
        pass
    return True

