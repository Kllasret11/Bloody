from aiogram import types
from aiogram.dispatcher import FSMContext

from filters.is_admin import IsAdminSession
from keyboards.reply import admin_menu, main_menu
from loader import bot, db, dp
from states import (
    AddBalanceState,
    AddCategoryState,
    AddProductState,
    AdminReplySosState,
    DeleteCategoryState,
    DeleteProductState,
    EditCategoryState,
    EditPriceState,
    EditProductState,
)


dp.filters_factory.bind(IsAdminSession)


def _order_delivery(order) -> str:
    if order["address"]:
        return str(order["address"])

    latitude = order.get("latitude")
    longitude = order.get("longitude")

    if latitude is not None and longitude is not None:
        return f"Геопозиция: {float(latitude):.6f}, {float(longitude):.6f}"

    return "-"


@dp.message_handler(IsAdminSession(), lambda m: m.text == "🚪 Выйти из админки", state="*")
async def admin_logout(message: types.Message, state: FSMContext) -> None:
    await db.set_admin_session(message.from_user.id, False)
    await state.finish()
    await message.answer("Ты вышел из админки.", reply_markup=main_menu())



# ДОБАВЛЕНИЕ КАТЕГОРИИ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "➕ Добавить категорию")
async def add_category_start(message: types.Message) -> None:
    await AddCategoryState.waiting_for_name.set()
    await message.answer("Введи название новой категории:")


@dp.message_handler(IsAdminSession(), state=AddCategoryState.waiting_for_name)
async def add_category_finish(message: types.Message, state: FSMContext) -> None:
    name = message.text.strip()
    await db.add_category(name)
    await state.finish()
    await message.answer(f"Категория <b>{name}</b> добавлена.", reply_markup=admin_menu())


# ДОБАВЛЕНИЕ ТОВАРА

@dp.message_handler(IsAdminSession(), lambda m: m.text == "➕ Добавить товар")
async def add_product_start(message: types.Message) -> None:
    await AddProductState.waiting_for_name.set()
    await message.answer("Введи название товара:")


@dp.message_handler(IsAdminSession(), state=AddProductState.waiting_for_name)
async def add_product_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await AddProductState.waiting_for_price.set()
    await message.answer("Введи цену товара:")


@dp.message_handler(IsAdminSession(), state=AddProductState.waiting_for_price)
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

    text = "Выбери ID категории:\n" + "\n".join(
        f"{c['id']} — {c['name']}" for c in categories
    )
    await AddProductState.waiting_for_category.set()
    await message.answer(text)


@dp.message_handler(IsAdminSession(), state=AddProductState.waiting_for_category)
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

    await state.update_data(category_id=category_id)
    await AddProductState.waiting_for_photo.set()
    await message.answer("Теперь отправь фото товара одним сообщением или напиши /skip, чтобы пропустить.")


@dp.message_handler(IsAdminSession(), commands=["skip"], state=AddProductState.waiting_for_photo)
async def add_product_skip_photo(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    await db.add_product(
        int(data["category_id"]),
        data["name"],
        float(data["price"]),
        None,
    )
    await state.finish()
    await message.answer("Товар добавлен без фото.", reply_markup=admin_menu())


@dp.message_handler(IsAdminSession(), content_types=types.ContentType.PHOTO, state=AddProductState.waiting_for_photo)
async def add_product_photo(message: types.Message, state: FSMContext) -> None:
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    await db.add_product(
        int(data["category_id"]),
        data["name"],
        float(data["price"]),
        photo_file_id,
    )
    await state.finish()
    await message.answer("Товар с фото добавлен.", reply_markup=admin_menu())


@dp.message_handler(IsAdminSession(), state=AddProductState.waiting_for_photo)
async def add_product_photo_invalid(message: types.Message) -> None:
    await message.answer("Отправь фото товара или напиши /skip.")



# БЫСТРОЕ ИЗМЕНЕНИЕ ЦЕНЫ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "💲 Изменить цену")
async def edit_price_start(message: types.Message) -> None:
    products = await db.get_all_products()
    if not products:
        await message.answer("Товаров пока нет.")
        return

    text = "Список товаров:\n" + "\n".join(
        f"{p['id']} — {p['name']} ({p['category_name']}) — {float(p['price']):.2f}"
        for p in products
    )
    await EditPriceState.waiting_for_product_id.set()
    await message.answer(text + "\n\nВведи ID товара:")


@dp.message_handler(IsAdminSession(), state=EditPriceState.waiting_for_product_id)
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


@dp.message_handler(IsAdminSession(), state=EditPriceState.waiting_for_new_price)
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



# ИЗМЕНЕНИЕ БАЛАНСА

@dp.message_handler(IsAdminSession(), lambda m: m.text == "💰 Изменить баланс")
async def add_balance_start(message: types.Message) -> None:
    await AddBalanceState.waiting_for_user_id.set()
    await message.answer("Введи Telegram ID пользователя:")


@dp.message_handler(IsAdminSession(), state=AddBalanceState.waiting_for_user_id)
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
    await message.answer("Введи сумму изменения баланса:")


@dp.message_handler(IsAdminSession(), state=AddBalanceState.waiting_for_amount)
async def add_balance_finish(message: types.Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    data = await state.get_data()
    await db.change_balance(int(data["user_id"]), amount)
    await state.finish()
    await message.answer("Баланс успешно изменён.", reply_markup=admin_menu())



# УДАЛЕНИЕ ТОВАРА

@dp.message_handler(IsAdminSession(), lambda m: m.text == "🗑 Удалить товар")
async def delete_product_start(message: types.Message) -> None:
    products = await db.get_all_products()
    if not products:
        await message.answer("Товаров пока нет.")
        return

    text = "Список товаров:\n" + "\n".join(
        f"{p['id']} — {p['name']} ({p['category_name']}) — {float(p['price']):.2f}"
        for p in products
    )

    await DeleteProductState.waiting_for_product_id.set()
    await message.answer(text + "\n\nВведи ID товара, который нужно удалить:")


@dp.message_handler(IsAdminSession(), state=DeleteProductState.waiting_for_product_id)
async def delete_product_finish(message: types.Message, state: FSMContext) -> None:
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID товара должен быть числом.")
        return

    product = await db.get_product(product_id)
    if not product:
        await message.answer("Товар не найден.")
        return

    await db.delete_product(product_id)
    await state.finish()
    await message.answer("Товар удалён.", reply_markup=admin_menu())



# УДАЛЕНИЕ КАТЕГОРИИ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "🗑 Удалить категорию")
async def delete_category_start(message: types.Message) -> None:
    categories = await db.get_categories()
    if not categories:
        await message.answer("Категорий пока нет.")
        return

    text = "Список категорий:\n" + "\n".join(
        f"{c['id']} — {c['name']}" for c in categories
    )

    await DeleteCategoryState.waiting_for_category_id.set()
    await message.answer(text + "\n\nВведи ID категории, которую нужно удалить:")


@dp.message_handler(IsAdminSession(), state=DeleteCategoryState.waiting_for_category_id)
async def delete_category_finish(message: types.Message, state: FSMContext) -> None:
    try:
        category_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID категории должен быть числом.")
        return

    category = await db.get_category(category_id)
    if not category:
        await message.answer("Категория не найдена.")
        return

    has_products = await db.category_has_products(category_id)
    if has_products:
        await message.answer("Нельзя удалить категорию, пока в ней есть товары.")
        return

    await db.delete_category(category_id)
    await state.finish()
    await message.answer("Категория удалена.", reply_markup=admin_menu())



# РЕДАКТИРОВАНИЕ КАТЕГОРИИ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "✏️ Редактировать категорию")
async def edit_category_start(message: types.Message) -> None:
    categories = await db.get_categories()
    if not categories:
        await message.answer("Категорий пока нет.")
        return

    text = "Список категорий:\n" + "\n".join(
        f"{c['id']} — {c['name']}" for c in categories
    )

    await EditCategoryState.waiting_for_category_id.set()
    await message.answer(text + "\n\nВведи ID категории, которую нужно переименовать:")


@dp.message_handler(IsAdminSession(), state=EditCategoryState.waiting_for_category_id)
async def edit_category_get_id(message: types.Message, state: FSMContext) -> None:
    try:
        category_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID категории должен быть числом.")
        return

    category = await db.get_category(category_id)
    if not category:
        await message.answer("Категория не найдена.")
        return

    await state.update_data(category_id=category_id)
    await EditCategoryState.waiting_for_new_name.set()
    await message.answer("Введи новое название категории:")


@dp.message_handler(IsAdminSession(), state=EditCategoryState.waiting_for_new_name)
async def edit_category_finish(message: types.Message, state: FSMContext) -> None:
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("Название слишком короткое.")
        return

    data = await state.get_data()
    await db.update_category_name(int(data["category_id"]), new_name)
    await state.finish()
    await message.answer("Категория обновлена.", reply_markup=admin_menu())



# РЕДАКТИРОВАНИЕ ТОВАРА

@dp.message_handler(IsAdminSession(), lambda m: m.text == "✏️ Редактировать товар")
async def edit_product_start(message: types.Message) -> None:
    products = await db.get_all_products()
    if not products:
        await message.answer("Товаров пока нет.")
        return

    text = "Список товаров:\n" + "\n".join(
        f"{p['id']} — {p['name']} ({p['category_name']}) — {float(p['price']):.2f}"
        for p in products
    )

    await EditProductState.waiting_for_product_id.set()
    await message.answer(
        text + "\n\nВведи ID товара, который хочешь изменить:"
    )


@dp.message_handler(IsAdminSession(), state=EditProductState.waiting_for_product_id)
async def edit_product_get_id(message: types.Message, state: FSMContext) -> None:
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
    await EditProductState.waiting_for_new_name.set()
    await message.answer("Введи новое название товара:")


@dp.message_handler(IsAdminSession(), state=EditProductState.waiting_for_new_name)
async def edit_product_name(message: types.Message, state: FSMContext) -> None:
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("Название слишком короткое.")
        return

    await state.update_data(new_name=new_name)
    await EditProductState.waiting_for_new_price.set()
    await message.answer("Введи новую цену товара:")


@dp.message_handler(IsAdminSession(), state=EditProductState.waiting_for_new_price)
async def edit_product_price(message: types.Message, state: FSMContext) -> None:
    try:
        new_price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Цена должна быть числом.")
        return

    await state.update_data(new_price=new_price)
    await EditProductState.waiting_for_new_category.set()

    categories = await db.get_categories()
    if not categories:
        await message.answer("Категории не найдены.")
        return

    text = "Выбери новый ID категории:\n" + "\n".join(
        f"{c['id']} — {c['name']}" for c in categories
    )
    await message.answer(text)


@dp.message_handler(IsAdminSession(), state=EditProductState.waiting_for_new_category)
async def edit_product_category(message: types.Message, state: FSMContext) -> None:
    try:
        category_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID категории должен быть числом.")
        return

    category = await db.get_category(category_id)
    if not category:
        await message.answer("Категория не найдена.")
        return

    await state.update_data(category_id=category_id)
    await EditProductState.waiting_for_new_photo.set()
    await message.answer("Отправь новое фото товара или напиши /skip, чтобы оставить старое.")


@dp.message_handler(IsAdminSession(), commands=["skip"], state=EditProductState.waiting_for_new_photo)
async def edit_product_skip_photo(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = int(data["product_id"])

    await db.update_product_name(product_id, data["new_name"])
    await db.update_product_price(product_id, float(data["new_price"]))
    await db.update_product_category(product_id, int(data["category_id"]))

    await state.finish()
    await message.answer("Товар обновлён.", reply_markup=admin_menu())


@dp.message_handler(IsAdminSession(), content_types=types.ContentType.PHOTO, state=EditProductState.waiting_for_new_photo)
async def edit_product_new_photo(message: types.Message, state: FSMContext) -> None:
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    product_id = int(data["product_id"])

    await db.update_product_name(product_id, data["new_name"])
    await db.update_product_price(product_id, float(data["new_price"]))
    await db.update_product_category(product_id, int(data["category_id"]))
    await db.update_product_photo(product_id, photo_file_id)

    await state.finish()
    await message.answer("Товар полностью обновлён.", reply_markup=admin_menu())


@dp.message_handler(IsAdminSession(), state=EditProductState.waiting_for_new_photo)
async def edit_product_photo_invalid(message: types.Message) -> None:
    await message.answer("Отправь фото товара или напиши /skip.")



# ЗАКАЗЫ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "📦 Заказы")
async def all_orders(message: types.Message) -> None:
    orders = await db.get_all_orders()
    if not orders:
        await message.answer("Заказов пока нет.")
        return

    lines = ["<b>Последние заказы</b>"]
    for order in orders:
        lines.append(
            f"№{order['id']} | user_id={order['user_id']} | "
            f"{float(order['total_amount']):.2f} | {order['status']}\n"
            f"📍 {_order_delivery(order)}\n"
            f"📞 {order['phone'] or '-'}"
        )

    await message.answer("\n\n".join(lines))


# СТАТИСТИКА

@dp.message_handler(IsAdminSession(), lambda m: m.text == "📊 Статистика")
async def admin_stats(message: types.Message) -> None:
    products = await db.get_all_products()
    orders = await db.get_all_orders()
    tickets = await db.get_open_tickets()

    text = (
        "<b>Статистика магазина</b>\n\n"
        f"🛍 Товаров: {len(products)}\n"
        f"📦 Заказов: {len(orders)}\n"
        f"🆘 Открытых обращений: {len(tickets)}"
    )

    await message.answer(text)


# SOS ОБРАЩЕНИЯ

@dp.message_handler(IsAdminSession(), lambda m: m.text == "🆘 Обращения")
async def all_tickets(message: types.Message) -> None:
    tickets = await db.get_open_tickets()
    if not tickets:
        await message.answer("Открытых обращений нет.")
        return

    lines = ["<b>Открытые обращения</b>"]
    for ticket in tickets:
        uname = f"@{ticket['username']}" if ticket['username'] else ticket['full_name']
        lines.append(
            f"ID {ticket['id']} | {uname} | user_id={ticket['user_id']}\n{ticket['message']}"
        )

    await message.answer("\n\n".join(lines))


@dp.message_handler(IsAdminSession(), lambda m: m.text == "✉️ Ответить на SOS")
async def reply_ticket_start(message: types.Message) -> None:
    tickets = await db.get_open_tickets()
    if not tickets:
        await message.answer("Открытых обращений нет.")
        return

    await AdminReplySosState.waiting_for_ticket_id.set()
    await message.answer("Введи ID обращения, на которое хочешь ответить:")


@dp.message_handler(IsAdminSession(), state=AdminReplySosState.waiting_for_ticket_id)
async def reply_ticket_id(message: types.Message, state: FSMContext) -> None:
    try:
        ticket_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID обращения должен быть числом.")
        return

    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Обращение не найдено.")
        return

    await state.update_data(ticket_id=ticket_id)
    await AdminReplySosState.waiting_for_reply.set()
    await message.answer("Введи ответ пользователю:")


@dp.message_handler(IsAdminSession(), state=AdminReplySosState.waiting_for_reply)
async def reply_ticket_finish(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    ticket = await db.get_ticket(int(data["ticket_id"]))

    if not ticket:
        await state.finish()
        await message.answer("Обращение не найдено.", reply_markup=admin_menu())
        return

    reply_text = message.text.strip()
    await db.answer_ticket(int(data["ticket_id"]), reply_text)
    await state.finish()

    try:
        await bot.send_message(
            int(ticket["user_id"]),
            f"💬 <b>Ответ по обращению #{ticket['id']}</b>\n\n{reply_text}",
        )
    except Exception:
        pass

    await message.answer("Ответ отправлен пользователю.", reply_markup=admin_menu())