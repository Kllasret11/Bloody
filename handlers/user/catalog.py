from aiogram import types

from keyboards.inline import categories_kb, products_kb
from loader import db, dp


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
    await call.message.answer("Товары категории:", reply_markup=products_kb(products))
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(call: types.CallbackQuery) -> None:
    product_id = int(call.data.split(":", 1)[1])
    await db.add_to_cart(call.from_user.id, product_id)
    await call.answer("Товар добавлен в корзину")
