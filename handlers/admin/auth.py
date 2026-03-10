from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import admin_menu
from loader import config, db, dp
from states import AdminAuthState


def _is_allowed_admin(user_id: int) -> bool:
    return user_id in config.admins


@dp.message_handler(commands=["admin"], state="*")
async def admin_login_start(message: types.Message, state: FSMContext) -> None:
    if not _is_allowed_admin(message.from_user.id):
        await message.answer("У тебя нет доступа к админке.")
        return
    await state.finish()
    await AdminAuthState.waiting_for_login.set()
    await message.answer("Введи логин администратора:")


@dp.message_handler(state=AdminAuthState.waiting_for_login)
async def admin_login_input(message: types.Message, state: FSMContext) -> None:
    await state.update_data(login=message.text.strip())
    await AdminAuthState.waiting_for_password.set()
    await message.answer("Введи пароль администратора:")


@dp.message_handler(state=AdminAuthState.waiting_for_password)
async def admin_password_input(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    login = data.get("login", "")
    password = message.text.strip()

    if login == config.admin_login and password == config.admin_password:
        await db.set_admin_session(message.from_user.id, True)
        await state.finish()
        await message.answer("Вход выполнен. Добро пожаловать в админ-панель.", reply_markup=admin_menu())
        return

    await state.finish()
    await message.answer("Неверный логин или пароль.")
