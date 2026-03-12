from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from keyboards.reply import back_menu
from loader import dp, db


class CategoryState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_edit_name = State()



def categories_menu_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("➕ Добавить категорию", callback_data="category_add"))
    kb.add(types.InlineKeyboardButton("📋 Список категорий", callback_data="category_list"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return kb



def category_back_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_categories"))
    return kb


@dp.callback_query_handler(lambda c: c.data == "admin_categories")
async def categories_menu(call: types.CallbackQuery):
    await call.message.edit_text("📂 <b>Управление категориями</b>", reply_markup=categories_menu_keyboard())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "category_add")
async def category_add_start(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await CategoryState.waiting_for_new_name.set()
    await call.message.edit_text("Введите название новой категории:", reply_markup=category_back_keyboard())
    await call.message.answer("Можно нажать ⬅ Назад внизу для отмены.", reply_markup=back_menu())
    await call.answer()


@dp.message_handler(state=CategoryState.waiting_for_new_name)
async def category_add_finish(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Название не может быть пустым.", reply_markup=back_menu())
        return

    created_id = await db.add_category(name)
    await state.finish()
    if created_id is None:
        await message.answer("⚠️ Такая категория уже существует.", reply_markup=categories_menu_keyboard())
        return

    await db.log_admin_action(message.from_user.id, "category_created", {"category_id": created_id, "name": name})
    await message.answer(f"✅ Категория <b>{name}</b> добавлена.", reply_markup=categories_menu_keyboard())


@dp.callback_query_handler(lambda c: c.data == "category_list")
async def category_list(call: types.CallbackQuery):
    categories = await db.get_categories()
    kb = types.InlineKeyboardMarkup(row_width=1)

    if not categories:
        kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_categories"))
        await call.message.edit_text("Категорий пока нет.", reply_markup=kb)
        await call.answer()
        return

    lines = ["📂 <b>Категории</b>\n"]
    for category in categories:
        lines.append(f"• {category['name']}")
        kb.add(types.InlineKeyboardButton(category["name"], callback_data=f"category_open:{category['id']}"))

    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_categories"))
    await call.message.edit_text("\n".join(lines), reply_markup=kb)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("category_open:"))
async def category_open(call: types.CallbackQuery):
    category_id = int(call.data.split(":", 1)[1])
    category = await db.get_category(category_id)
    if not category:
        await call.answer("Категория не найдена", show_alert=True)
        return

    products = await db.get_products_by_category(category_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✏️ Переименовать", callback_data=f"category_edit:{category_id}"))
    if not products:
        kb.add(types.InlineKeyboardButton("❌ Удалить", callback_data=f"category_delete:{category_id}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="category_list"))

    text = (
        f"📂 <b>{category['name']}</b>\n\n"
        f"Товаров в категории: <b>{len(products)}</b>\n"
    )
    if products:
        text += "\nЧтобы удалить категорию, сначала перенеси или удали товары из неё."

    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("category_edit:"))
async def category_edit_start(call: types.CallbackQuery, state: FSMContext):
    category_id = int(call.data.split(":", 1)[1])
    await state.finish()
    await state.update_data(category_id=category_id)
    await CategoryState.waiting_for_edit_name.set()
    await call.message.edit_text("Введите новое название категории:", reply_markup=category_back_keyboard())
    await call.message.answer("Можно нажать ⬅ Назад внизу для отмены.", reply_markup=back_menu())
    await call.answer()


@dp.message_handler(state=CategoryState.waiting_for_edit_name)
async def category_edit_finish(message: types.Message, state: FSMContext):
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("❌ Название не может быть пустым.", reply_markup=back_menu())
        return

    data = await state.get_data()
    category_id = int(data["category_id"])
    await db.update_category_name(category_id, new_name)
    await db.log_admin_action(message.from_user.id, "category_updated", {"category_id": category_id, "name": new_name})
    await state.finish()
    await message.answer(f"✅ Категория обновлена: <b>{new_name}</b>", reply_markup=categories_menu_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith("category_delete:"))
async def category_delete(call: types.CallbackQuery):
    category_id = int(call.data.split(":", 1)[1])
    category = await db.get_category(category_id)
    if not category:
        await call.answer("Категория не найдена", show_alert=True)
        return

    if await db.category_has_products(category_id):
        await call.answer("Нельзя удалить категорию с товарами.", show_alert=True)
        return

    await db.delete_category(category_id)
    await db.log_admin_action(call.from_user.id, "category_deleted", {"category_id": category_id, "name": category['name']})
    await call.message.edit_text("❌ Категория удалена.", reply_markup=category_back_keyboard())
    await call.answer()
