from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import dp, db, config


class AddAdminState(StatesGroup):
    waiting_for_user_id = State()


def admins_menu_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить администратора", callback_data="admin_add"))
    keyboard.add(types.InlineKeyboardButton("📋 Список администраторов", callback_data="admin_list"))
    keyboard.add(types.InlineKeyboardButton("➖ Удалить администратора", callback_data="admin_remove"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


def admins_back_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_admins"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "admin_admins")
async def admins_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "🛠 <b>Управление администраторами</b>",
        reply_markup=admins_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_add")
async def add_admin_start(call: types.CallbackQuery, state: FSMContext):
    await AddAdminState.waiting_for_user_id.set()

    await call.message.edit_text(
        "Введите <b>user_id</b> пользователя, которого нужно сделать администратором:",
        reply_markup=admins_back_keyboard(),
    )
    await call.answer()


@dp.message_handler(state=AddAdminState.waiting_for_user_id)
async def add_admin_finish(message: types.Message, state: FSMContext):
    raw_user_id = (message.text or "").strip()

    if not raw_user_id.isdigit():
        await message.answer("❌ user_id должен быть числом.")
        return

    user_id = int(raw_user_id)

    await db.add_admin(user_id)
    await state.finish()

    await message.answer(
        f"✅ Пользователь <code>{user_id}</code> добавлен в администраторы.",
        reply_markup=admins_menu_keyboard(),
    )


@dp.callback_query_handler(lambda c: c.data == "admin_list")
async def admin_list(call: types.CallbackQuery):
    admins = await db.list_admins()

    lines = ["🛠 <b>Список администраторов</b>\n"]

    if config.super_admin_id:
        lines.append(f"• <code>{config.super_admin_id}</code> — SUPER ADMIN")

    if admins:
        for admin in admins:
            user_id = int(admin["user_id"])
            if user_id == config.super_admin_id:
                continue
            lines.append(f"• <code>{user_id}</code>")
    else:
        if not config.super_admin_id:
            lines.append("❌ Администраторов нет.")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=admins_back_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_remove")
async def admin_remove_menu(call: types.CallbackQuery):
    admins = await db.list_admins()

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    added_any = False
    for admin in admins:
        user_id = int(admin["user_id"])

        if user_id == config.super_admin_id:
            continue

        keyboard.add(
            types.InlineKeyboardButton(
                text=f"❌ {user_id}",
                callback_data=f"admin_delete:{user_id}",
            )
        )
        added_any = True

    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_admins"))

    if not added_any:
        await call.message.edit_text(
            "❌ Нет администраторов для удаления.",
            reply_markup=keyboard,
        )
        await call.answer()
        return

    await call.message.edit_text(
        "Выберите администратора для удаления:",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_delete:"))
async def admin_delete(call: types.CallbackQuery):
    user_id = int(call.data.split(":", 1)[1])

    if user_id == config.super_admin_id:
        await call.answer("❌ Нельзя удалить супер администратора.", show_alert=True)
        return

    await db.remove_admin(user_id)

    await call.message.edit_text(
        f"❌ Администратор <code>{user_id}</code> удалён.",
        reply_markup=admins_back_keyboard(),
    )
    await call.answer("Администратор удалён")