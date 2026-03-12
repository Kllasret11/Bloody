from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import back_menu
from loader import dp, db
from states import ProductCreateState


def products_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="product_add"))
    keyboard.add(types.InlineKeyboardButton("📋 Список товаров", callback_data="product_list"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


def back_to_products_keyboard(target: str = "admin_products"):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data=target))
    return keyboard


def product_card_keyboard(product_id: int):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("✏️ Название", callback_data=f"product_edit_name:{product_id}"),
        types.InlineKeyboardButton("📝 Описание", callback_data=f"product_edit_description:{product_id}"),
    )
    keyboard.row(
        types.InlineKeyboardButton("💰 Цена", callback_data=f"product_edit_price:{product_id}"),
        types.InlineKeyboardButton("📦 Остаток", callback_data=f"product_edit_stock:{product_id}"),
    )
    keyboard.row(
        types.InlineKeyboardButton("📂 Категория", callback_data=f"product_edit_category:{product_id}"),
        types.InlineKeyboardButton("📷 Фото", callback_data=f"product_edit_photo:{product_id}"),
    )
    keyboard.row(
        types.InlineKeyboardButton("🙈 Скрыть/Показать", callback_data=f"product_toggle:{product_id}"),
        types.InlineKeyboardButton("❌ Скрыть", callback_data=f"product_remove:{product_id}"),
    )
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="product_list"))
    return keyboard


def categories_choose_keyboard(categories, back_target: str = "admin_products"):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for category in categories:
        keyboard.add(types.InlineKeyboardButton(category['name'], callback_data=f"product_pick_category:{category['id']}"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data=back_target))
    return keyboard


async def _render_product(call_or_message, product_id: int, edit: bool = False):
    product = await db.fetchrow(
        """
        SELECT p.id, p.name, p.description, p.price, p.stock, p.photo_file_id, p.is_active, c.name as category_name
        FROM products p
        JOIN categories c ON c.id = p.category_id
        WHERE p.id = $1
        """,
        product_id,
    )
    if not product:
        if isinstance(call_or_message, types.CallbackQuery):
            await call_or_message.answer("Товар не найден", show_alert=True)
        else:
            await call_or_message.answer("Товар не найден")
        return

    status = "Активен" if product['is_active'] else "Скрыт"
    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📂 Категория: <b>{product['category_name']}</b>\n"
        f"📝 Описание: {product['description'] or '-'}\n"
        f"💰 Цена: {float(product['price']):.2f}\n"
        f"📦 Остаток: {int(product['stock'])}\n"
        f"👁 Статус: {status}"
    )

    kb = product_card_keyboard(product_id)
    if isinstance(call_or_message, types.CallbackQuery):
        await call_or_message.message.edit_text(text, reply_markup=kb)
        await call_or_message.answer()
    else:
        await call_or_message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == "admin_products")
async def admin_products(call: types.CallbackQuery):
    await call.message.edit_text("🛍 <b>Управление товарами</b>", reply_markup=products_menu_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "product_add")
async def product_add_start(call: types.CallbackQuery, state: FSMContext):
    categories = await db.get_categories()
    if not categories:
        await call.answer("Сначала создай категорию", show_alert=True)
        return
    await state.finish()
    await state.update_data(scope="admin")
    await ProductCreateState.waiting_for_category.set()
    await call.message.edit_text("📂 Выбери категорию товара:", reply_markup=categories_choose_keyboard(categories))
    await call.message.answer("Можно нажать ⬅ Назад внизу, чтобы отменить создание товара.", reply_markup=back_menu())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_pick_category:"), state=ProductCreateState.waiting_for_category)
async def product_pick_category(call: types.CallbackQuery, state: FSMContext):
    category_id = int(call.data.split(':')[1])
    await state.update_data(category_id=category_id)
    await ProductCreateState.waiting_for_name.set()
    await call.message.edit_text("✏️ Введите название товара:", reply_markup=back_to_products_keyboard())
    await call.answer()


@dp.message_handler(state=ProductCreateState.waiting_for_name)
async def product_add_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name or name == "⬅ Назад":
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
    raw_price = (message.text or "").strip().replace(',', '.')
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
    await state.update_data(stock=int(raw_stock))
    await ProductCreateState.waiting_for_photo.set()
    await message.answer("📷 Отправьте фото товара или напишите '-' чтобы пропустить.", reply_markup=back_menu())


@dp.message_handler(content_types=types.ContentType.PHOTO, state=ProductCreateState.waiting_for_photo)
async def product_add_photo(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    product_id = await db.add_product(
        int(data['category_id']),
        data['name'],
        float(data['price']),
        photo_file_id=photo_file_id,
        stock=int(data['stock']),
        description=data.get('description') or None,
    )
    await db.log_admin_action(message.from_user.id, 'product_created', {'product_id': product_id, 'name': data['name']})
    await state.finish()
    await message.answer(f"✅ Товар <b>{data['name']}</b> добавлен.")


@dp.message_handler(state=ProductCreateState.waiting_for_photo)
async def product_add_finish_no_photo(message: types.Message, state: FSMContext):
    text = (message.text or '').strip().lower()
    if text not in {'-', 'нет', 'skip', 'пропустить'}:
        await message.answer("Отправь фото или напиши '-' чтобы пропустить.")
        return
    data = await state.get_data()
    product_id = await db.add_product(
        int(data['category_id']),
        data['name'],
        float(data['price']),
        photo_file_id=None,
        stock=int(data['stock']),
        description=data.get('description') or None,
    )
    await db.log_admin_action(message.from_user.id, 'product_created', {'product_id': product_id, 'name': data['name']})
    await state.finish()
    await message.answer(f"✅ Товар <b>{data['name']}</b> добавлен.")


@dp.callback_query_handler(lambda c: c.data == "product_list")
async def product_list(call: types.CallbackQuery):
    products = await db.get_all_products()
    if not products:
        await call.message.edit_text("❌ Товаров нет", reply_markup=back_to_products_keyboard())
        await call.answer()
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    text = "🛍 <b>Список товаров</b>\n\n"
    for product in products:
        status = "скрыт" if not product['is_active'] else ("нет в наличии" if int(product['stock']) <= 0 else "в наличии")
        text += f"• {product['name']} — {float(product['price']):.2f} | {product['category_name']} | {status}\n"
        keyboard.add(types.InlineKeyboardButton(product['name'], callback_data=f"product_open:{product['id']}"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_products"))
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_open:"))
async def product_open(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])
    await _render_product(call, product_id, edit=True)


@dp.callback_query_handler(lambda c: c.data.startswith("product_toggle:"))
async def product_toggle(call: types.CallbackQuery):
    product_id = int(call.data.split(':')[1])
    product = await db.get_product(product_id)
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return
    await db.set_product_active(product_id, not bool(product['is_active']))
    await db.log_admin_action(call.from_user.id, 'product_toggled', {'product_id': product_id, 'is_active': not bool(product['is_active'])})
    await _render_product(call, product_id, edit=True)


@dp.callback_query_handler(lambda c: c.data.startswith("product_remove:"))
async def product_remove(call: types.CallbackQuery):
    product_id = int(call.data.split(':')[1])
    await db.set_product_active(product_id, False)
    await db.log_admin_action(call.from_user.id, 'product_hidden', {'product_id': product_id})
    await call.message.edit_text("❌ Товар скрыт.", reply_markup=back_to_products_keyboard('product_list'))
    await call.answer()
