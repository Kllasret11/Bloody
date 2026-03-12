from aiogram import types
from aiogram.dispatcher.filters import Command

from loader import dp, db, config
from keyboards.admin import (
    admin_main_keyboard,
    admin_catalog_keyboard,
    admin_finance_keyboard,
    admin_communications_keyboard,
)


def admin_panel_keyboard() -> types.InlineKeyboardMarkup:
    return admin_main_keyboard()


def promo_menu_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Создать промокод", callback_data="promo_create"))
    keyboard.add(types.InlineKeyboardButton("📋 Список промокодов", callback_data="promo_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Удалить промокод", callback_data="promo_delete"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_finance"))
    return keyboard


def admin_users_keyboard(users) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for user in users:
        title = user["full_name"]
        if user["username"]:
            title += f" (@{user['username']})"
        keyboard.add(
            types.InlineKeyboardButton(
                title,
                callback_data=f"admin_user_open:{user['user_id']}",
            )
        )

    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


def admin_user_card_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("💰 Баланс", callback_data="admin_balance"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
    )
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_users"))
    return keyboard


async def has_admin_access(user_id: int) -> bool:
    if user_id == config.super_admin_id:
        return True
    if user_id in config.admins:
        return True
    return await db.is_admin(user_id)


@dp.message_handler(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id

    if not await has_admin_access(user_id):
        await message.answer("❌ У вас нет доступа к админ панели")
        return

    await db.set_admin_session(user_id, True)
    await message.answer("⚙️ <b>Админ панель</b>", reply_markup=admin_main_keyboard())


@dp.callback_query_handler(lambda c: c.data == "admin_back")
async def back_admin(call: types.CallbackQuery):
    await call.message.edit_text("⚙️ <b>Админ панель</b>", reply_markup=admin_main_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_catalog")
async def admin_catalog(call: types.CallbackQuery):
    await call.message.edit_text("🛍 <b>Каталог</b>", reply_markup=admin_catalog_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_finance")
async def admin_finance(call: types.CallbackQuery):
    await call.message.edit_text("💳 <b>Финансы</b>", reply_markup=admin_finance_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_communications")
async def admin_communications(call: types.CallbackQuery):
    await call.message.edit_text("📢 <b>Коммуникации</b>", reply_markup=admin_communications_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_promos")
async def promo_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "🎟 <b>Управление промокодами</b>",
        reply_markup=promo_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    users = await db.fetchval("SELECT COUNT(*) FROM users")
    orders = await db.fetchval("SELECT COUNT(*) FROM orders")
    products = await db.fetchval("SELECT COUNT(*) FROM products WHERE is_active = TRUE")
    revenue = await db.fetchval(
        """
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE status IN ('completed', 'done')
        """
    )

    text = (
        "📊 <b>Статистика магазина</b>\n\n"
        f"👥 Пользователей: <b>{int(users or 0)}</b>\n"
        f"📦 Заказов: <b>{int(orders or 0)}</b>\n"
        f"🛍 Товаров: <b>{int(products or 0)}</b>\n"
        f"💰 Оборот: <b>{float(revenue or 0):.2f}</b>"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_users")
async def admin_users(call: types.CallbackQuery):
    users = await db.list_users(limit=20, offset=0)

    if not users:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
        await call.message.edit_text(
            "👥 <b>Пользователей пока нет</b>",
            reply_markup=keyboard,
        )
        await call.answer()
        return

    text_lines = ["👥 <b>Пользователи</b>\n"]
    for user in users:
        username = f" (@{user['username']})" if user["username"] else ""
        text_lines.append(
            f"• {user['full_name']}{username} — <code>{user['user_id']}</code>"
        )

    await call.message.edit_text(
        "\n".join(text_lines),
        reply_markup=admin_users_keyboard(users),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_user_open:"))
async def admin_user_open(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])

    user = await db.get_user(user_id)
    if not user:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_users"))
        await call.message.edit_text(
            "❌ Пользователь не найден",
            reply_markup=keyboard,
        )
        await call.answer()
        return

    orders = await db.get_user_orders(user_id)
    orders_count = len(orders)
    total_spent = sum(float(order["total_amount"]) for order in orders)

    username = f"@{user['username']}" if user["username"] else "—"

    text = (
        "👤 <b>Карточка пользователя</b>\n\n"
        f"🪪 <b>ID:</b> <code>{user['user_id']}</code>\n"
        f"👤 <b>Имя:</b> {user['full_name']}\n"
        f"🔹 <b>Username:</b> {username}\n"
        f"💰 <b>Баланс:</b> {float(user['balance']):.2f}\n"
        f"📦 <b>Заказов:</b> {orders_count}\n"
        f"💸 <b>Потратил:</b> {total_spent:.2f}"
    )

    await call.message.edit_text(
        text,
        reply_markup=admin_user_card_keyboard(user_id),
    )
    await call.answer()
