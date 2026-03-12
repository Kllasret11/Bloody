from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from keyboards.reply import back_menu
from loader import db, dp


class ProductCreateState(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_stock = State()
    waiting_for_category = State()


def products_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="product_add"))
    keyboard.add(types.InlineKeyboardButton("📋 Список товаров", callback_data="product_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Удалить товар", callback_data="product_delete_menu"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


def back_to_products_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
    return keyboard


def categories_keyboard(categories):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for category in categories:
        keyboard.add(
            types.InlineKeyboardButton(
                category["name"],
                callback_data=f"product_category:{int(category['id'])}",
            )
        )
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "admin_products")
async def admin_products(call: types.CallbackQuery):
    await call.message.edit_text(
        "🛍 <b>Управление товарами</b>",
        reply_markup=products_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "product_add")
async def product_add_start(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await ProductCreateState.waiting_for_name.set()
    await call.message.edit_text(
        "✏️ Введите название товара:",
        reply_markup=back_to_products_keyboard(),
    )
    await call.message.answer("Можно нажать ⬅ Назад внизу, чтобы отменить создание товара.", reply_markup=back_menu())
    await call.answer()


@dp.message_handler(lambda m: (m.text or "").strip() == "⬅ Назад", state=ProductCreateState.waiting_for_name)
@dp.message_handler(lambda m: (m.text or "").strip() == "⬅ Назад", state=ProductCreateState.waiting_for_description)
@dp.message_handler(lambda m: (m.text or "").strip() == "⬅ Назад", state=ProductCreateState.waiting_for_price)
@dp.message_handler(lambda m: (m.text or "").strip() == "⬅ Назад", state=ProductCreateState.waiting_for_stock)
async def product_add_back(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("↩️ Возврат в управление товарами.", reply_markup=products_menu_keyboard())


@dp.message_handler(state=ProductCreateState.waiting_for_name)
async def product_add_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()

    if not name:
        await message.answer("❌ Название товара не может быть пустым.")
        return

    await state.update_data(name=name)
    await ProductCreateState.waiting_for_description.set()
    await message.answer("📝 Введите описание товара:", reply_markup=back_menu())


@dp.message_handler(state=ProductCreateState.waiting_for_description)
async def product_add_description(message: types.Message, state: FSMContext):
    description = (message.text or "").strip()

    await state.update_data(description=description)
    await ProductCreateState.waiting_for_price.set()
    await message.answer("💰 Введите цену товара:", reply_markup=back_menu())


@dp.message_handler(state=ProductCreateState.waiting_for_price)
async def product_add_price(message: types.Message, state: FSMContext):
    raw_price = (message.text or "").strip().replace(",", ".")

    try:
        price = float(raw_price)
    except ValueError:
        await message.answer("❌ Цена должна быть числом.")
        return

    if price <= 0:
        await message.answer("❌ Цена должна быть больше 0.")
        return

    await state.update_data(price=price)
    await ProductCreateState.waiting_for_stock.set()
    await message.answer("📦 Введите количество товара на складе:", reply_markup=back_menu())


@dp.message_handler(state=ProductCreateState.waiting_for_stock)
async def product_add_stock(message: types.Message, state: FSMContext):
    raw_stock = (message.text or "").strip()

    if not raw_stock.isdigit():
        await message.answer("❌ Количество должно быть целым числом.")
        return

    stock = int(raw_stock)
    await state.update_data(stock=stock)

    categories = await db.get_categories()
    if not categories:
        await state.finish()
        await message.answer(
            "❌ Нельзя добавить товар без категории. Сначала создай хотя бы одну категорию.",
            reply_markup=products_menu_keyboard(),
        )
        return

    await ProductCreateState.waiting_for_category.set()
    await message.answer(
        "📂 Выберите категорию для товара:",
        reply_markup=categories_keyboard(categories),
    )


@dp.callback_query_handler(lambda c: c.data.startswith("product_category:"), state=ProductCreateState.waiting_for_category)
async def product_choose_category(call: types.CallbackQuery, state: FSMContext):
    category_id = int(call.data.split(":", 1)[1])
    category = await db.get_category(category_id)
    if not category:
        await call.answer("Категория не найдена", show_alert=True)
        return

    data = await state.get_data()
    name = data["name"]
    description = data.get("description", "")
    price = float(data["price"])
    stock = int(data["stock"])

    await db.execute(
        """
        INSERT INTO products (category_id, name, description, price, stock, is_active)
        VALUES ($1, $2, $3, $4, $5, TRUE)
        """,
        category_id,
        name,
        description,
        price,
        stock,
    )

    await state.finish()

    await call.message.edit_text(
        f"✅ Товар <b>{name}</b> добавлен.\n\n"
        f"📂 Категория: {category['name']}\n"
        f"📝 Описание: {description or '-'}\n"
        f"💰 Цена: {price:.2f}\n"
        f"📦 Остаток: {stock}",
        reply_markup=products_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "product_list")
async def product_list(call: types.CallbackQuery):
    products = await db.fetch(
        """
        SELECT p.id, p.name, p.description, p.price, p.stock, c.name AS category_name
        FROM products p
        JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = TRUE
        ORDER BY p.id DESC
        """
    )

    if not products:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
        await call.message.edit_text(
            "❌ Товаров нет",
            reply_markup=keyboard,
        )
        await call.answer()
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    text = "🛍 <b>Список товаров</b>\n\n"

    for product in products:
        text += (
            f"• {product['name']} — {float(product['price']):.2f}"
            f" | Остаток: {int(product['stock'])}"
            f" | Категория: {product['category_name']}\n"
        )

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
        SELECT p.id, p.name, p.description, p.price, p.stock, c.name AS category_name
        FROM products p
        JOIN categories c ON c.id = p.category_id
        WHERE p.id = $1
        """,
        product_id,
    )

    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📂 Категория: {product['category_name']}\n"
        f"📝 Описание: {product['description'] or '-'}\n"
        f"💰 Цена: {float(product['price']):.2f}\n"
        f"📦 Остаток: {int(product['stock'])}"
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


@dp.callback_query_handler(lambda c: c.data == "product_delete_menu")
async def product_delete_menu(call: types.CallbackQuery):
    products = await db.fetch(
        """
        SELECT id, name
        FROM products
        WHERE is_active = TRUE
        ORDER BY id DESC
        """
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if not products:
        keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
        await call.message.edit_text("❌ Товаров нет.", reply_markup=keyboard)
        await call.answer()
        return

    for product in products:
        keyboard.add(
            types.InlineKeyboardButton(
                f"❌ {product['name']}",
                callback_data=f"product_remove:{product['id']}",
            )
        )

    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))

    await call.message.edit_text(
        "Выберите товар для удаления:",
        reply_markup=keyboard,
    )
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

    await call.message.edit_text(
        "❌ Товар удалён (скрыт из каталога).",
        reply_markup=products_menu_keyboard(),
    )
    await call.answer()
