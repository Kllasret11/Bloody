from aiogram import types

from keyboards.inline import categories_kb, product_item_kb
from loader import db, dp


@dp.message_handler(commands=["menu"])
@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message):
    categories = await db.get_categories()

    if not categories:
        await message.answer("Категории пока не добавлены.")
        return

    await message.answer(
        "Выбери категорию:",
        reply_markup=categories_kb(categories)
    )


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
            f"💰 Цена: {price:.2f}"
        )

        if photo:
            await call.message.answer_photo(
                photo,
                caption=caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )
        else:
            await call.message.answer(
                caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )

    await call.answer()


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

    await call.answer(f"Добавлено в корзину: {quantity} шт.")