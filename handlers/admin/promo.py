from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from keyboards.common import back_menu
from loader import dp, db


class PromoCreateState(StatesGroup):
    waiting_for_code = State()
    waiting_for_percent = State()


def promo_back_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_promos"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "promo_create")
async def promo_create_start(call: types.CallbackQuery, state: FSMContext):
    await PromoCreateState.waiting_for_code.set()
    await call.message.edit_text(
        "✏️ Введите название промокода\n\nПример: <code>SALE10</code>",
        reply_markup=promo_back_keyboard(),
    )
    await call.answer()


@dp.message_handler(state=PromoCreateState.waiting_for_code)
async def promo_create_code(message: types.Message, state: FSMContext):
    code = (message.text or "").strip().upper()

    if not code:
        await message.answer("❌ Название промокода не может быть пустым.")
        return

    await state.update_data(code=code)
    await PromoCreateState.waiting_for_percent.set()

    await message.answer("💸 Введите процент скидки\n\nПример: <code>10</code>")


@dp.message_handler(state=PromoCreateState.waiting_for_percent)
async def promo_create_percent(message: types.Message, state: FSMContext):
    raw_percent = (message.text or "").strip()

    if not raw_percent.isdigit():
        await message.answer("❌ Процент скидки должен быть числом.")
        return

    percent = int(raw_percent)
    if percent < 1 or percent > 100:
        await message.answer("❌ Процент скидки должен быть от 1 до 100.")
        return

    data = await state.get_data()
    code = data["code"]

    await db.create_promo(code=code, percent=percent)

    await state.finish()

    await message.answer(
        f"✅ <b>Промокод создан</b>\n\n"
        f"🏷 Код: <code>{code}</code>\n"
        f"💸 Скидка: <b>{percent}%</b>",
        reply_markup=promo_back_keyboard(),
    )


@dp.callback_query_handler(lambda c: c.data == "promo_list")
async def promo_list(call: types.CallbackQuery):
    promos = await db.get_all_promos()

    if not promos:
        text = "❌ Промокодов пока нет."
    else:
        lines = ["🎟 <b>Промокоды</b>\n"]
        for promo in promos:
            status = "✅ Активен" if promo["is_active"] else "❌ Отключён"
            used_count = int(promo["used_count"] or 0)
            lines.append(
                f"• <code>{promo['code']}</code> — <b>{promo['percent']}%</b>\n"
                f"  {status} | использован: {used_count}"
            )
        text = "\n".join(lines)

    await call.message.edit_text(
        text,
        reply_markup=promo_back_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "promo_delete")
async def promo_delete_menu(call: types.CallbackQuery):
    promos = await db.get_all_promos()
    active_promos = [promo for promo in promos if promo["is_active"]]

    if not active_promos:
        await call.message.edit_text(
            "❌ Нет активных промокодов для удаления.",
            reply_markup=promo_back_keyboard(),
        )
        await call.answer()
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for promo in active_promos:
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"❌ {promo['code']}",
                callback_data=f"promo_remove:{promo['code']}",
            )
        )

    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_promos"))

    await call.message.edit_text(
        "Выберите промокод, который нужно отключить:",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("promo_remove:"))
async def promo_remove(call: types.CallbackQuery):
    code = call.data.split(":", 1)[1]

    await db.deactivate_promo(code)

    await call.message.edit_text(
        f"❌ Промокод <code>{code}</code> отключён.",
        reply_markup=promo_back_keyboard(),
    )
    await call.answer("Промокод отключён")