from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from loader import db


class IsAdminSession(BoundFilter):
    key = "is_admin_session"

    async def check(self, message: Message) -> bool:
        return await db.is_admin_logged_in(message.from_user.id)