from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from keyboards.reply import back_menu
from loader import dp, db


class BalanceState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()


def balance_menu_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Начислить баланс", callback_data="balance_add"))
    keyboard.add(types.InlineKeyboardButton("➖ Списать баланс", callback_data="balance_remove"))
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


def balance_back_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_balance"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "admin_balance")
async def balance_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "💰 <b>Управление балансом</b>",
        reply_markup=balance_menu_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "balance_add")
async def balance_add_start(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(action="add")
    await BalanceState.waiting_for_user_id.set()

    await call.message.edit_text(
        "Введите <b>user_id</b> пользователя,\nкоторому нужно начислить баланс:",
        reply_markup=balance_back_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "balance_remove")
async def balance_remove_start(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(action="remove")
    await BalanceState.waiting_for_user_id.set()

    await call.message.edit_text(
        "Введите <b>user_id</b> пользователя,\nу которого нужно списать баланс:",
        reply_markup=balance_back_keyboard(),
    )
    await call.answer()


@dp.message_handler(state=BalanceState.waiting_for_user_id)
async def balance_get_user(message: types.Message, state: FSMContext):
    raw_user_id = (message.text or "").strip()

    if not raw_user_id.isdigit():
        await message.answer("❌ user_id должен быть числом.")
        return

    await state.update_data(user_id=int(raw_user_id))
    await BalanceState.waiting_for_amount.set()

    await message.answer("Введите сумму:", reply_markup=back_menu())


@dp.message_handler(state=BalanceState.waiting_for_amount)
async def balance_apply(message: types.Message, state: FSMContext):
    raw_amount = (message.text or "").strip().replace(",", ".")

    try:
        amount = float(raw_amount)
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0.")
        return

    data = await state.get_data()
    user_id = int(data["user_id"])
    action = data["action"]

    if action == "remove":
        amount = -amount

    await db.change_balance(user_id, amount)
    await state.finish()

    if amount > 0:
        text = (
            f"✅ <b>Баланс начислен</b>\n\n"
            f"🪪 User ID: <code>{user_id}</code>\n"
            f"💰 Сумма: <b>+{amount:.2f}</b>"
        )
    else:
        text = (
            f"➖ <b>Баланс списан</b>\n\n"
            f"🪪 User ID: <code>{user_id}</code>\n"
            f"💰 Сумма: <b>{amount:.2f}</b>"
        )

    await message.answer(text, reply_markup=balance_menu_keyboard())