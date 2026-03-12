from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import main_menu
from keyboards.admin.reply import admin_menu
from loader import dp, db


@dp.message_handler(lambda m: m.text == "⬅ Назад", state="*")
async def universal_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await message.answer("Ты уже в меню.", reply_markup=main_menu())
        return

    data = await state.get_data()
    is_admin = str(data.get("scope") or "") == "admin" or await db.is_admin_logged_in(message.from_user.id)
    await state.finish()

    if is_admin:
        await message.answer("↩ Возврат в админ-панель.", reply_markup=admin_menu())
    else:
        await message.answer("↩ Возврат в главное меню.", reply_markup=main_menu())
