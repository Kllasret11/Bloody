from aiogram import types
from loader import dp, db


def products_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="product_add"))
    keyboard.add(types.InlineKeyboardButton("📋 Список товаров", callback_data="product_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Удалить товар", callback_data="product_delete"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "admin_products")
async def admin_products(call: types.CallbackQuery):
    await call.message.edit_text(
        "🛍 <b>Управление товарами</b>",
        reply_markup=products_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "product_list")
async def product_list(call: types.CallbackQuery):
    products = await db.fetch(
        """
        SELECT id, name, price
        FROM products
        WHERE is_active = TRUE
        ORDER BY id DESC
        """
    )

    if not products:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
        await call.message.edit_text(
            "❌ Товаров нет",
            reply_markup=keyboard,
        )
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    text = "🛍 <b>Список товаров</b>\n\n"

    for product in products:
        text += f"• {product['name']} — {float(product['price']):.2f}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                product["name"],
                callback_data=f"product_open:{product['id']}",
            )
        )

    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_open:"))
async def product_open(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])

    product = await db.fetchrow(
        """
        SELECT id, name, description, price
        FROM products
        WHERE id = $1
        """,
        product_id,
    )

    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📝 Описание: {product['description'] or '-'}\n"
        f"💰 Цена: {float(product['price']):.2f}"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Удалить товар",
            callback_data=f"product_remove:{product_id}",
        )
    )
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="product_list"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_remove:"))
async def product_remove(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])

    await db.execute(
        """
        UPDATE products
        SET is_active = FALSE
        WHERE id = $1
        """,
        product_id,
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="product_list"))

    await call.message.edit_text(
        "❌ Товар удалён",
        reply_markup=keyboard,
    )
    await call.answer()