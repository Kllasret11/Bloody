from aiogram import types
from aiogram.utils.exceptions import MessageNotModified

from keyboards.inline import categories_kb, product_item_kb
from loader import db, dp
from utils.cooldown import hit


@dp.message_handler(commands=["menu"])
@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message):
    categories = await db.get_categories()
    if not categories:
        await message.answer("Категории пока не добавлены.")
        return
    text = "<b>🛍 Каталог магазина</b>\n\nВыбери категорию:"
    await message.answer(text, reply_markup=categories_kb(categories))


@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def show_products(call: types.CallbackQuery):
    category_id = int(call.data.split(":")[1])
    products = await db.fetch(
        """
        SELECT id, name, description, price, photo_file_id, stock
        FROM products
        WHERE category_id = $1 AND is_active = TRUE
        ORDER BY id DESC
        """,
        category_id,
    )

    if not products:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    for product in products:
        name = product.get("name", "Товар")
        price = float(product.get("price", 0))
        photo = product.get("photo_file_id")
        stock = int(product.get("stock") or 0)
        description = (product.get("description") or "").strip()
        stock_line = "❌ Нет в наличии" if stock <= 0 else f"📦 В наличии: {stock}"
        caption = f"<b>{name}</b>\n💰 Цена: <b>{price:.2f}</b>\n{stock_line}"
        if description:
            caption += f"\n\n📝 {description}"
        if stock > 0:
            caption += "\n\nВыберите количество:"

        markup = product_item_kb(int(product["id"]), 1) if stock > 0 else None
        if photo:
            await call.message.answer_photo(photo=photo, caption=caption, reply_markup=markup)
        else:
            await call.message.answer(caption, reply_markup=markup)

    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("qty_plus:"))
async def qty_plus(call: types.CallbackQuery):
    if not hit(call.from_user.id, "qty_plus", 0.2):
        await call.answer("Слишком часто.", show_alert=False)
        return
    _, product_id, qty = call.data.split(":")
    product_id = int(product_id)
    qty = int(qty) + 1
    product = await db.get_product(product_id)
    if product and int(product["stock"]) > 0:
        qty = min(qty, int(product["stock"]))
    try:
        await call.message.edit_reply_markup(reply_markup=product_item_kb(product_id, qty))
    except MessageNotModified:
        pass
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("qty_minus:"))
async def qty_minus(call: types.CallbackQuery):
    if not hit(call.from_user.id, "qty_minus", 0.2):
        await call.answer("Слишком часто.", show_alert=False)
        return
    _, product_id, qty = call.data.split(":")
    product_id = int(product_id)
    qty = max(1, int(qty) - 1)
    try:
        await call.message.edit_reply_markup(reply_markup=product_item_kb(product_id, qty))
    except MessageNotModified:
        pass
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(call: types.CallbackQuery):
    if not hit(call.from_user.id, "addcart", 0.5):
        await call.answer("Слишком часто.", show_alert=False)
        return
    parts = call.data.split(":")
    product_id = int(parts[1])
    quantity = int(parts[2]) if len(parts) > 2 else 1
    product = await db.get_product_available(product_id)
    if not product:
        await call.answer("Товара нет в наличии.", show_alert=True)
        return
    if quantity > int(product["stock"]):
        await call.answer("Нельзя добавить больше, чем есть на складе.", show_alert=True)
        return
    await db.add_to_cart(call.from_user.id, product_id, quantity)
    await call.answer(f"🛒 Добавлено в корзину: {quantity} шт.")
