from __future__ import annotations

import time
import traceback
from typing import Optional

from loader import bot, config

_last_sent_at: float = 0.0


async def notify_admins(text: str, *, cooldown_seconds: int = 30) -> None:
    global _last_sent_at
    now = time.time()
    if now - _last_sent_at < cooldown_seconds:
        return
    _last_sent_at = now

    for admin_id in config.admins:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            continue


def format_exception(exc: BaseException) -> str:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(tb) > 3500:
        tb = tb[-3500:]
    return tb

