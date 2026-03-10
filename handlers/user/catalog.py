from aiogram import types

from keyboards.inline import categories_kb, product_item_kb
from loader import db, dp


<<<<<<< HEAD
# ===== ОТКРЫТЬ КАТАЛОГ =====
=======
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
@dp.message_handler(commands=["menu"])
@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message):

    categories = await db.get_categories()

    if not categories:
        await message.answer("Категории пока не добавлены.")
        return

<<<<<<< HEAD
    text = "<b>🛍 Каталог магазина</b>\n\nВыбери категорию:"

    await message.answer(
        text,
=======
    await message.answer(
        "Выбери категорию:",
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
        reply_markup=categories_kb(categories)
    )


<<<<<<< HEAD
# ===== ПОКАЗАТЬ ТОВАРЫ =====
=======
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def show_products(call: types.CallbackQuery):

    category_id = int(call.data.split(":")[1])

    products = await db.get_products_by_category(category_id)

    if not products:
        await call.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    for product in products:

        name = product.get("name", "Товар")
        price = float(product.get("price", 0))
        photo = product.get("photo_file_id")

        caption = (
            f"<b>{name}</b>\n"
<<<<<<< HEAD
            f"💰 Цена: <b>{price:.2f}</b>\n\n"
            f"Выберите количество:"
        )

        if photo:

            await call.message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )

        else:

=======
            f"💰 Цена: {price:.2f}"
        )

        if photo:
            await call.message.answer_photo(
                photo,
                caption=caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )
        else:
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
            await call.message.answer(
                caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )

    await call.answer()


# ===== УВЕЛИЧЕНИЕ КОЛИЧЕСТВА =====
@dp.callback_query_handler(lambda c: c.data.startswith("qty_plus"))
async def qty_plus(call: types.CallbackQuery):

    _, product_id, qty = call.data.split(":")

    product_id = int(product_id)
    qty = int(qty) + 1

    await call.message.edit_reply_markup(
        reply_markup=product_item_kb(product_id, qty)
    )

    await call.answer()


# ===== УМЕНЬШЕНИЕ КОЛИЧЕСТВА =====
@dp.callback_query_handler(lambda c: c.data.startswith("qty_minus"))
async def qty_minus(call: types.CallbackQuery):

    _, product_id, qty = call.data.split(":")

    product_id = int(product_id)
    qty = max(1, int(qty) - 1)

    await call.message.edit_reply_markup(
        reply_markup=product_item_kb(product_id, qty)
    )

    await call.answer()


<<<<<<< HEAD
# ===== ДОБАВИТЬ В КОРЗИНУ =====
=======
# ===== ДОБАВЛЕНИЕ В КОРЗИНУ =====
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
@dp.callback_query_handler(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(call: types.CallbackQuery):

    data = call.data.split(":")

    if len(data) == 3:
        _, product_id, quantity = data
    else:
        _, product_id = data
        quantity = 1

    product_id = int(product_id)
    quantity = int(quantity)

    await db.add_to_cart(call.from_user.id, product_id, quantity)

<<<<<<< HEAD
    await call.answer(f"🛒 Добавлено в корзину: {quantity} шт.")
=======
    await call.answer(f"Добавлено в корзину: {quantity} шт.")
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
