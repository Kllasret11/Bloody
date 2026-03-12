from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from keyboards.reply import admin_menu
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


async def _has_admin_access(user_id: int) -> bool:
    if user_id == config.super_admin_id:
        return True

    if user_id in config.admins:
        return True

    return await db.is_admin(user_id)


async def _send_admin_reply_menu(message: types.Message):
    await message.answer("⚙️ Админ панель", reply_markup=admin_menu())


@dp.message_handler(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id

    if not await _has_admin_access(user_id):
        await message.answer("❌ У вас нет доступа к админ панели")
        return

    await db.set_admin_session(user_id, True)
    await _send_admin_reply_menu(message)


@dp.message_handler(lambda m: (m.text or "").strip() == "📊 Статистика")
async def admin_stats_text(message: types.Message):
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
    await message.answer(text, reply_markup=admin_menu())


@dp.message_handler(lambda m: (m.text or "").strip() == "📦 Заказы")
async def admin_orders_text(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("🆕 Активные заказы", callback_data="admin_orders_active"))
    keyboard.add(types.InlineKeyboardButton("🕘 Архив заказов", callback_data="admin_orders_archive"))
    await message.answer("📦 <b>Управление заказами</b>", reply_markup=keyboard)


@dp.message_handler(lambda m: (m.text or "").strip() == "👥 Пользователи")
async def admin_users_text(message: types.Message):
    users = await db.list_users(limit=20, offset=0)

    if not users:
        await message.answer("👥 <b>Пользователей пока нет</b>", reply_markup=admin_menu())
        return

    text_lines = ["👥 <b>Пользователи</b>\n"]
    for user in users:
        username = f" (@{user['username']})" if user["username"] else ""
        text_lines.append(f"• {user['full_name']}{username} — <code>{user['user_id']}</code>")

    await message.answer("\n".join(text_lines), reply_markup=admin_users_keyboard(users))


@dp.message_handler(lambda m: (m.text or "").strip() == "🔎 Найти пользователя")
async def admin_find_user_text(message: types.Message):
    await message.answer(
        "🔎 Поиск пользователя пока не подключён.\n\n"
        "Пока используй раздел <b>👥 Пользователи</b>.",
        reply_markup=admin_menu(),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "➕ Добавить товар")
async def admin_add_product_text(message: types.Message, state: FSMContext):
    from .products import ProductCreateState
    await state.finish()
    await ProductCreateState.waiting_for_name.set()
    await message.answer("✏️ Введите название товара:")
    await message.answer("Можно нажать ⬅ Назад внизу, чтобы отменить создание товара.")


@dp.message_handler(lambda m: (m.text or "").strip() == "➕ Добавить категорию")
async def admin_add_category_text(message: types.Message, state: FSMContext):
    from .categories import CategoryState
    await state.finish()
    await CategoryState.waiting_for_new_name.set()
    await message.answer("Введите название новой категории:")


@dp.message_handler(lambda m: (m.text or "").strip() == "✏️ Редактировать товар")
async def admin_edit_product_text(message: types.Message):
    await message.answer(
        "✏️ Редактирование товара открывается через список товаров.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📋 Список товаров", callback_data="product_list")
        ),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "✏️ Редактировать категорию")
async def admin_edit_category_text(message: types.Message):
    await message.answer(
        "✏️ Выбери категорию из списка, чтобы переименовать.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📋 Список категорий", callback_data="category_list")
        ),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "🗑 Удалить товар")
async def admin_delete_product_text(message: types.Message):
    await message.answer(
        "🗑 Выбери товар для удаления.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ Открыть удаление товаров", callback_data="product_delete_menu")
        ),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "🗑 Удалить категорию")
async def admin_delete_category_text(message: types.Message):
    await message.answer(
        "🗑 Удаление категории открывается через список категорий.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📋 Список категорий", callback_data="category_list")
        ),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "💲 Изменить цену")
async def admin_change_price_text(message: types.Message):
    await message.answer(
        "💲 Изменение цены пока открывается через товары.\n"
        "Сначала выбери товар из списка.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📋 Список товаров", callback_data="product_list")
        ),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "💰 Изменить баланс")
async def admin_change_balance_text(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Начислить баланс", callback_data="balance_add"))
    keyboard.add(types.InlineKeyboardButton("➖ Списать баланс", callback_data="balance_remove"))
    await message.answer("💰 <b>Управление балансом</b>", reply_markup=keyboard)


@dp.message_handler(lambda m: (m.text or "").strip() == "🆘 Обращения")
async def admin_sos_text(message: types.Message):
    await message.answer(
        "🆘 Раздел обращений пока не подключён в новой панели.",
        reply_markup=admin_menu(),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "✉️ Ответить на SOS")
async def admin_reply_sos_text(message: types.Message):
    await message.answer(
        "✉️ Ответ на SOS пока не подключён в новой панели.",
        reply_markup=admin_menu(),
    )


@dp.message_handler(lambda m: (m.text or "").strip() == "🚪 Выйти из админки")
async def admin_exit_text(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🚪 Ты вышел из админки.", reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query_handler(lambda c: c.data == "admin_back")
async def back_admin(call: types.CallbackQuery):
    await call.message.answer("⚙️ Админ панель", reply_markup=admin_menu())
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
        text_lines.append(f"• {user['full_name']}{username} — <code>{user['user_id']}</code>")

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

    await call.message.edit_text(text, reply_markup=admin_user_card_keyboard(user_id))
    await call.answer()
