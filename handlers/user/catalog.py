from aiogram import types

from keyboards.inline import MAX_QTY, MIN_QTY, categories_kb, product_item_kb
from loader import db, dp


@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message) -> None:
    categories = await db.get_categories()
    if not categories:
        await message.answer("Категории пока не добавлены.")
        return
    await message.answer("Выбери категорию:", reply_markup=categories_kb(categories))


@dp.callback_query_handler(lambda c: c.data == "qty:noop")
async def quantity_noop(call: types.CallbackQuery) -> None:
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def show_products(call: types.CallbackQuery) -> None:
    category_id = int(call.data.split(":", 1)[1])
    products = await db.get_products_by_category(category_id)

    if not products:
        await call.message.answer("В этой категории пока нет товаров.")
        await call.answer()
        return

    for product in products:
        caption = (
            f"<b>{product['name']}</b>\n"
            f"{product['description'] or ''}\n\n"
            f"💰 Цена: {float(product['price']):.2f}\n"
            f"📦 В наличии: {product['stock']}"
        )

        if product.get("photo_file_id"):
            await call.message.answer_photo(
                product["photo_file_id"],
                caption=caption,
                reply_markup=product_item_kb(int(product["id"]), qty=1),
            )
        else:
            await call.message.answer(
                caption,
                reply_markup=product_item_kb(int(product["id"]), qty=1),
            )

    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("qty:"))
async def change_quantity(call: types.CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 4:
        await call.answer("Ошибка количества", show_alert=True)
        return

    _, product_id, qty, action = parts
    product_id = int(product_id)
    qty = int(qty)

    if action == "plus":
        qty = min(MAX_QTY, qty + 1)
    elif action == "minus":
        qty = max(MIN_QTY, qty - 1)

    await call.message.edit_reply_markup(reply_markup=product_item_kb(product_id, qty))
    await call.answer(f"Количество: {qty}")


@dp.callback_query_handler(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(call: types.CallbackQuery) -> None:
    parts = call.data.split(":")

    if len(parts) == 3:
        _, product_id, quantity = parts
    elif len(parts) == 2:
        # поддержка старых кнопок без количества
        _, product_id = parts
        quantity = 1
    else:
        await call.answer("Некорректные данные товара", show_alert=True)
        return

    product_id = int(product_id)
    quantity = int(quantity)

    await db.add_to_cart(call.from_user.id, product_id, quantity)
    await call.answer(f"Товар добавлен в корзину: {quantity} шт.")