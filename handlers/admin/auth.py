from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import admin_menu
from loader import dp, config


@dp.message_handler(commands=["admin"])
async def admin_login(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in config.admins:
        await state.finish()
        await message.answer(
            "⚙️ Админ панель",
            reply_markup=admin_menu()
        )
        return

    await message.answer("❌ У вас нет доступа к админ панели")
