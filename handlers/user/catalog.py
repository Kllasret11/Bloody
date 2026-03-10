from aiogram import types

from keyboards.inline import categories_kb, product_item_kb
from loader import db, dp


@dp.message_handler(commands=["menu"])
@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message) -> None:
    categories = await db.get_categories()
    if not categories:
        await message.answer("Категории пока не добавлены.")
        return
    await message.answer("Выбери категорию:", reply_markup=categories_kb(categories))


@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def show_products(call: types.CallbackQuery) -> None:
    category_id = int(call.data.split(":", 1)[1])
    products = await db.get_products_by_category(category_id)
    if not products:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    for product in products:
        caption = f"<b>{product['name']}</b>\n💵 Цена: {float(product['price']):.2f}"
        if product["photo_file_id"]:
            await call.message.answer_photo(
                product["photo_file_id"],
                caption=caption,
                reply_markup=product_item_kb(int(product["id"])),
            )
        else:
            await call.message.answer(caption, reply_markup=product_item_kb(int(product["id"])))
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(call: types.CallbackQuery) -> None:
    product_id = int(call.data.split(":", 1)[1])
    await db.add_to_cart(user_id, product_id, quantity)
    await call.answer("Товар добавлен в корзину")

@dp.callback_query_handler(lambda c: c.data.startswith("qty_plus"))
async def qty_plus(call: types.CallbackQuery):
    _, product_id, qty = call.data.split(":")
    qty = int(qty) + 1
    await call.message.edit_reply_markup(reply_markup=quantity_kb(int(product_id), qty))

@dp.callback_query_handler(lambda c: c.data.startswith("qty_minus"))
async def qty_minus(call: types.CallbackQuery):
    _, product_id, qty = call.data.split(":")
    qty = max(1, int(qty) - 1)
    await call.message.edit_reply_markup(reply_markup=quantity_kb(int(product_id), qty))