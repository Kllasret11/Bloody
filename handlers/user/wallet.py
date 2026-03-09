from aiogram import types

from loader import db, dp


@dp.message_handler(lambda m: m.text == "💰 Баланс")
async def show_balance(message: types.Message) -> None:
    user = await db.get_user(message.from_user.id)
    balance_value = float(user["balance"]) if user else 0.0
    await message.answer(f"Твой баланс: <b>{balance_value:.2f}</b>")
