from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, config
from .panel import admin_panel_keyboard


@dp.message_handler(commands=["admin"])
async def admin_login(message: types.Message, state: FSMContext):

    user_id = message.from_user.id

    if user_id in config.admins:
        await message.answer(
            "⚙️ Админ панель",
            reply_markup=admin_panel_keyboard()
        )
        return

    await message.answer("❌ У вас нет доступа к админ панели")
