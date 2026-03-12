from aiogram import types

from keyboards.reply import main_menu
from loader import dp, db


@dp.message_handler(lambda m: m.text == "💰 Баланс")
async def wallet(message: types.Message):
    user = await db.get_user(message.from_user.id)
    balance = float(user['balance']) if user else 0.0
    await message.answer(f"💰 Твой баланс: <b>{balance:.2f}</b>", reply_markup=main_menu())
