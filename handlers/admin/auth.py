from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
from .panel import admin_panel_keyboard, has_admin_access


@dp.message_handler(commands=["admin"])
async def admin_login(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if await has_admin_access(user_id):
        await message.answer(
            "⚙️ Админ панель",
            reply_markup=admin_panel_keyboard()
        )
        return

    await message.answer("❌ У вас нет доступа к админ панели")
