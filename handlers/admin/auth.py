from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import dp, config, db


class AdminAuthState(StatesGroup):
    waiting_login = State()
    waiting_password = State()


async def _is_admin(user_id: int) -> bool:
    if user_id == config.super_admin_id:
        return True

    if user_id in config.admins:
        return True

    return await db.is_admin(user_id)


@dp.message_handler(Command("admin"))
async def admin_login_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if await _is_admin(user_id):
        await db.set_admin_session(user_id, True)
        await message.answer("✅ Вы уже авторизованы как администратор.")
        return

    await AdminAuthState.waiting_login.set()
    await message.answer("Введите логин администратора:")


@dp.message_handler(state=AdminAuthState.waiting_login)
async def admin_login_enter(message: types.Message, state: FSMContext):
    if message.text != config.admin_login:
        await message.answer("❌ Неверный логин.")
        await state.finish()
        return

    await state.update_data(login_ok=True)
    await AdminAuthState.waiting_password.set()

    await message.answer("Введите пароль:")


@dp.message_handler(state=AdminAuthState.waiting_password)
async def admin_password_enter(message: types.Message, state: FSMContext):
    if message.text != config.admin_password:
        await message.answer("❌ Неверный пароль.")
        await state.finish()
        return

    user_id = message.from_user.id

    await db.add_admin(user_id)
    await db.set_admin_session(user_id, True)

    await state.finish()

    await message.answer("✅ Авторизация администратора успешна.")