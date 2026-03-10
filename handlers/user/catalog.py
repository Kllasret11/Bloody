from aiogram import types

from keyboards.inline import categories_kb, product_item_kb
from loader import db, dp


# ===== ОТКРЫТЬ КАТАЛОГ =====

@dp.message_handler(commands=["menu"])
@dp.message_handler(lambda m: m.text == "🛍 Каталог")
async def show_categories(message: types.Message):
    categories = await db.get_categories()

    if not categories:
        await message.answer("Категории пока не добавлены.")
        return

    text = "<b>🛍 Каталог магазина</b>\n\nВыбери категорию:"

    await message.answer(
        text,
        reply_markup=categories_kb(categories)
    )


# ===== ПОКАЗАТЬ ТОВАРЫ =====

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
            await call.message.answer(
                caption,
                reply_markup=product_item_kb(int(product["id"]), 1)
            )

    await call.answer()


# ===== УВЕЛИЧЕНИЕ КОЛИЧЕСТВА =====

@dp.callback_query_handler(lambda c: c.data.startswith("qty_plus:"))
async def qty_plus(call: types.CallbackQuery):
    _, product_id, qty = call.data.split(":")

    product_id = int(product_id)
    qty = int(qty) + 1

    await call.message.edit_reply_markup(
        reply_markup=product_item_kb(product_id, qty)
    )

    await call.answer()


# ===== УМЕНЬШЕНИЕ КОЛИЧЕСТВА =====

@dp.callback_query_handler(lambda c: c.data.startswith("qty_minus:"))
async def qty_minus(call: types.CallbackQuery):
    _, product_id, qty = call.data.split(":")

    product_id = int(product_id)
    qty = max(1, int(qty) - 1)

    await call.message.edit_reply_markup(
        reply_markup=product_item_kb(product_id, qty)
    )

    await call.answer()


# ===== ДОБАВЛЕНИЕ В КОРЗИНУ =====

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

    await call.answer(f"🛒 Добавлено в корзину: {quantity} шт.")