from aiogram import types
from aiogram.dispatcher.filters import Command

from loader import dp, db, config


def admin_panel_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("📦 Заказы", callback_data="admin_orders"),
        types.InlineKeyboardButton("🛍 Товары", callback_data="admin_products"),
    )
    keyboard.row(
        types.InlineKeyboardButton("📂 Категории", callback_data="admin_categories"),
        types.InlineKeyboardButton("🎟 Промокоды", callback_data="admin_promos"),
    )
    keyboard.row(
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="admin_balance"),
    )
    keyboard.row(
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🛠 Администраторы", callback_data="admin_admins"),
    )
    keyboard.row(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
    )
    return keyboard


def promo_menu_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Создать промокод", callback_data="promo_create"))
    keyboard.add(types.InlineKeyboardButton("📋 Список промокодов", callback_data="promo_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Удалить промокод", callback_data="promo_delete"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


async def _has_admin_access(user_id: int) -> bool:
    if user_id == config.super_admin_id:
        return True

    if user_id in config.admins:
        return True

    return await db.is_admin(user_id)


@dp.message_handler(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id

    if not await _has_admin_access(user_id):
        await message.answer("❌ У вас нет доступа к админ панели")
        return

    await db.set_admin_session(user_id, True)

    await message.answer(
        "⚙️ <b>Админ панель</b>",
        reply_markup=admin_panel_keyboard(),
    )


@dp.callback_query_handler(lambda c: c.data == "admin_back")
async def back_admin(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚙️ <b>Админ панель</b>",
        reply_markup=admin_panel_keyboard(),
    )
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