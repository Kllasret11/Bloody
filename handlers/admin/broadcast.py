import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from keyboards.reply import back_menu
from loader import dp, db, bot


class BroadcastState(StatesGroup):
    waiting_for_message = State()


def broadcast_back_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == "admin_broadcast")
async def broadcast_start(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await BroadcastState.waiting_for_message.set()

    await call.message.edit_text(
        "📢 <b>Введите сообщение для рассылки</b>\n\n"
        "Оно будет отправлено всем пользователям, которые когда-либо запускали бота.",
        reply_markup=broadcast_back_keyboard(),
    )
    await call.message.answer("Можно нажать ⬅ Назад внизу для отмены.", reply_markup=back_menu())
    await call.answer()


@dp.message_handler(state=BroadcastState.waiting_for_message)
async def broadcast_send(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()

    if not text:
        await message.answer("❌ Сообщение не может быть пустым.", reply_markup=back_menu())
        return

    users = await db.fetch("SELECT user_id FROM users ORDER BY created_at ASC")

    success = 0
    failed = 0

    for user in users:
        user_id = int(user["user_id"])
        try:
            await bot.send_message(user_id, text)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await state.finish()

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))

    await message.answer(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Успешно отправлено: <b>{success}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>",
        reply_markup=keyboard,
    )
