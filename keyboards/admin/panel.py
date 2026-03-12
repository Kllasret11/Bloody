from aiogram import types


def admin_main_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📦 Заказы", callback_data="admin_orders"),
    )
    kb.row(
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("🛍 Каталог", callback_data="admin_catalog"),
    )
    kb.row(
        types.InlineKeyboardButton("💳 Финансы", callback_data="admin_finance"),
        types.InlineKeyboardButton("📢 Коммуникации", callback_data="admin_communications"),
    )
    kb.row(
        types.InlineKeyboardButton("🛠 Админы", callback_data="admin_admins"),
    )
    return kb


def admin_catalog_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("🛍 Товары", callback_data="admin_products"),
        types.InlineKeyboardButton("📂 Категории", callback_data="admin_categories"),
    )
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return kb


def admin_finance_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("💰 Баланс", callback_data="admin_balance"),
        types.InlineKeyboardButton("🎟 Промокоды", callback_data="admin_promos"),
    )
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return kb


def admin_communications_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return kb
