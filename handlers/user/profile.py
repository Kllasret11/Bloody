from aiogram import types

from keyboards.reply import main_menu
from loader import dp, db, bot
from services.referrals import referral_summary_text


@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Профиль пока не найден. Нажми /start ещё раз.", reply_markup=main_menu())
        return

    orders = await db.get_user_orders(message.from_user.id)
    total_spent = sum(float(order["total_amount"]) for order in orders)
    username = f"@{user['username']}" if user["username"] else "—"
    text = (
        "<b>👤 Профиль</b>\n\n"
        f"🪪 ID: <code>{user['user_id']}</code>\n"
        f"👤 Имя: {user['full_name']}\n"
        f"🔹 Username: {username}\n"
        f"💰 Баланс: <b>{float(user['balance']):.2f}</b>\n"
        f"📦 Заказов: <b>{len(orders)}</b>\n"
        f"💸 Потрачено: <b>{total_spent:.2f}</b>"
    )
    await message.answer(text, reply_markup=main_menu())


@dp.message_handler(lambda m: m.text == "👥 Рефералы")
async def referrals(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Профиль пока не найден. Нажми /start ещё раз.", reply_markup=main_menu())
        return

    stats = await db.get_referral_stats(message.from_user.id)
    me = await bot.get_me()
    text = referral_summary_text(user, stats, me.username or "your_bot")
    await message.answer(text, reply_markup=main_menu())
