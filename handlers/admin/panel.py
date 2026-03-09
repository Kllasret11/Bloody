from aiogram import types
from aiogram.dispatcher import FSMContext

from filters.is_admin import IsAdminSession
from keyboards.reply import admin_menu, main_menu
from loader import db, dp
from states import AddBalanceState, AddCategoryState, AddProductState, EditPriceState


dp.filters_factory.bind(IsAdminSession)


@dp.message_handler(lambda m: m.text == "🚪 Выйти из админки", state="*")
async def admin_logout(message: types.Message, state: FSMContext) -> None:
    await db.set_admin_session(message.from_user.id, False)
    await state.finish()
    await message.answer("Ты вышел из админки.", reply_markup=main_menu())


@dp.message_handler(lambda m: m.text == "➕ Добавить категорию")
async def add_category_start(message: types.Message) -> None:
    await AddCategoryState.waiting_for_name.set()
    await message.answer("Введи название новой категории:")


@dp.message_handler(state=AddCategoryState.waiting_for_name)
async def add_category_finish(message: types.Message, state: FSMContext) -> None:
    name = message.text.strip()
    await db.add_category(name)
    await state.finish()
    await message.answer(f"Категория <b>{name}</b> добавлена.", reply_markup=admin_menu())


@dp.message_handler(lambda m: m.text == "➕ Добавить товар")
async def add_product_start(message: types.Message) -> None:
    await AddProductState.waiting_for_name.set()
    await message.answer("Введи название товара:")


@dp.message_handler(state=AddProductState.waiting_for_name)
async def add_product_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await AddProductState.waiting_for_price.set()
    await message.answer("Введи цену товара:")


@dp.message_handler(state=AddProductState.waiting_for_price)
async def add_product_price(message: types.Message, state: FSMContext) -> None:
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Цена должна быть числом.")
        return
    await state.update_data(price=price)
    categories = await db.get_categories()
    if not categories:
        await state.finish()
        await message.answer("Сначала добавь хотя бы одну категорию.", reply_markup=admin_menu())
        return
    text = "Выбери ID категории:\n" + "\n".join(f"{c['id']} — {c['name']}" for c in categories)
    await AddProductState.waiting_for_category.set()
    await message.answer(text)


@dp.message_handler(state=AddProductState.waiting_for_category)
async def add_product_category(message: types.Message, state: FSMContext) -> None:
    try:
        category_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID категории должен быть числом.")
        return
    category = await db.get_category(category_id)
    if not category:
        await message.answer("Категория не найдена.")
        return
    data = await state.get_data()
    await db.add_product(category_id, data["name"], float(data["price"]))
    await state.finish()
    await message.answer("Товар добавлен.", reply_markup=admin_menu())


@dp.message_handler(lambda m: m.text == "💲 Изменить цену")
async def edit_price_start(message: types.Message) -> None:
    products = await db.get_all_products()
    if not products:
        await message.answer("Товаров пока нет.")
        return
    text = "Список товаров:\n" + "\n".join(
        f"{p['id']} — {p['name']} ({p['category_name']}) — {float(p['price']):.2f}" for p in products
    )
    await EditPriceState.waiting_for_product_id.set()
    await message.answer(text + "\n\nВведи ID товара:")


@dp.message_handler(state=EditPriceState.waiting_for_product_id)
async def edit_price_product(message: types.Message, state: FSMContext) -> None:
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID товара должен быть числом.")
        return
    product = await db.get_product(product_id)
    if not product:
        await message.answer("Товар не найден.")
        return
    await state.update_data(product_id=product_id)
    await EditPriceState.waiting_for_new_price.set()
    await message.answer("Введи новую цену:")


@dp.message_handler(state=EditPriceState.waiting_for_new_price)
async def edit_price_finish(message: types.Message, state: FSMContext) -> None:
    try:
        new_price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Цена должна быть числом.")
        return
    data = await state.get_data()
    await db.update_product_price(int(data["product_id"]), new_price)
    await state.finish()
    await message.answer("Цена обновлена.", reply_markup=admin_menu())


@dp.message_handler(lambda m: m.text == "💳 Пополнить баланс")
async def add_balance_start(message: types.Message) -> None:
    await AddBalanceState.waiting_for_user_id.set()
    await message.answer("Введи Telegram ID пользователя:")


@dp.message_handler(state=AddBalanceState.waiting_for_user_id)
async def add_balance_user(message: types.Message, state: FSMContext) -> None:
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом.")
        return
    user = await db.get_user(user_id)
    if not user:
        await message.answer("Пользователь не найден. Он должен сначала нажать /start.")
        return
    await state.update_data(user_id=user_id)
    await AddBalanceState.waiting_for_amount.set()
    await message.answer("Введи сумму пополнения:")


@dp.message_handler(state=AddBalanceState.waiting_for_amount)
async def add_balance_finish(message: types.Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return
    data = await state.get_data()
    await db.change_balance(int(data["user_id"]), amount)
    await state.finish()
    await message.answer("Баланс успешно пополнен.", reply_markup=admin_menu())


@dp.message_handler(lambda m: m.text == "📋 Все товары")
async def all_products(message: types.Message) -> None:
    products = await db.get_all_products()
    if not products:
        await message.answer("Товаров пока нет.")
        return
    lines = ["<b>Все товары</b>"]
    for p in products:
        lines.append(f"{p['id']} — {p['name']} — {p['category_name']} — {float(p['price']):.2f}")
    await message.answer("\n".join(lines))


@dp.message_handler(lambda m: m.text == "📑 Все заказы")
async def all_orders(message: types.Message) -> None:
    orders = await db.get_all_orders()
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    lines = ["<b>Последние заказы</b>"]
    for order in orders:
        lines.append(
            f"№{order['id']} | user_id={order['user_id']} | {float(order['total_amount']):.2f} | {order['status']}"
        )
    await message.answer("\n".join(lines))
