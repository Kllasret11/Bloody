from aiogram import types
from aiogram.types import InputFile

from loader import db, dp


@dp.message_handler(commands=["profile"])
@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def show_profile(message: types.Message) -> None:
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        user = await db.get_user(message.from_user.id)

    balance_value = float(user["balance"]) if user else 0.0
    text = (
        "<b>Профиль</b>\n\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"💰 Баланс: {balance_value:.2f}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>"
    )

    photo = InputFile("assets/profile_banner.png")
    await message.answer_photo(photo=photo, caption=text)
