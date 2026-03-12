from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from filters.is_admin import IsAdmin
from states import BroadcastStates


def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("⬅ Назад"))
    return kb


async def send_admin_panel(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📦 Заказы", callback_data="admin_orders"),
    )
    kb.add(
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("🔎 Найти пользователя", callback_data="admin_find_user"),
    )
    kb.add(
        types.InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_product"),
        types.InlineKeyboardButton("➕ Добавить категорию", callback_data="admin_add_category"),
    )
    kb.add(
        types.InlineKeyboardButton("✏️ Редактировать товар", callback_data="admin_edit_product"),
        types.InlineKeyboardButton("✏️ Редактировать категорию", callback_data="admin_edit_category"),
    )
    kb.add(
        types.InlineKeyboardButton("🗑 Удалить товар", callback_data="admin_delete_product"),
        types.InlineKeyboardButton("🗑 Удалить категорию", callback_data="admin_delete_category"),
    )
    kb.add(
        types.InlineKeyboardButton("💲 Изменить цену", callback_data="admin_change_price"),
        types.InlineKeyboardButton("💰 Изменить баланс", callback_data="admin_change_balance"),
    )
    kb.add(
        types.InlineKeyboardButton("🆘 Обращения", callback_data="admin_sos"),
        types.InlineKeyboardButton("✉️ Ответить на SOS", callback_data="admin_reply_sos"),
    )
    kb.add(types.InlineKeyboardButton("🚪 Выйти из админки", callback_data="admin_exit"))

    await message.answer("Админ панель", reply_markup=kb)


@dp.callback_query_handler(IsAdmin(), text="admin_broadcast")
async def broadcast_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.message)

    await call.message.answer(
        (
            "📢 <b>Введите сообщение для рассылки</b>\n\n"
            "Оно будет отправлено всем пользователям, которые когда-либо запускали бота."
        ),
        reply_markup=back_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@dp.message_handler(IsAdmin(), text="⬅ Назад", state=BroadcastStates.message)
async def broadcast_back(message: types.Message, state: FSMContext):
    await state.finish()
    await send_admin_panel(message)


@dp.message_handler(IsAdmin(), state=BroadcastStates.message)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.text == "⬅ Назад":
        await state.finish()
        await send_admin_panel(message)
        return

    users = await db.get_all_users()
    success = 0
    failed = 0

    for user in users:
        try:
            user_id = int(user["user_id"]) if isinstance(user, dict) else int(user[0])
            await bot.send_message(user_id, message.text)
            success += 1
        except Exception:
            failed += 1

    await state.finish()

    await message.answer(
        (
            f"✅ Рассылка завершена\n\n"
            f"Успешно отправлено: {success}\n"
            f"Ошибок: {failed}"
        )
    )
    await send_admin_panel(message)