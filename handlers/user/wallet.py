from aiogram import types
from aiogram.types import InputFile
<<<<<<< HEAD
import os
=======
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81

from loader import db, dp


@dp.message_handler(commands=["profile"])
@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def show_profile(message: types.Message) -> None:
<<<<<<< HEAD

    # создаём пользователя если его нет
    user = await db.get_user(message.from_user.id)

    if not user:
        await db.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name
        )
        user = await db.get_user(message.from_user.id)

    balance = float(user["balance"])

    # получаем заказы
    orders = await db.get_user_orders(message.from_user.id)
    orders_count = len(orders)

    text = (
        f"<b>👤 Профиль пользователя</b>\n\n"
        f"🧑 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"💰 Баланс: <b>{balance:.2f}</b>\n"
        f"📦 Заказов: <b>{orders_count}</b>"
    )

    banner_path = "assets/profile_banner.png"

    # если баннер есть
    if os.path.exists(banner_path):
        photo = InputFile(banner_path)
        await message.answer_photo(photo=photo, caption=text)
    else:
        await message.answer(text)
=======
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
>>>>>>> 89904677af75836394a197c014783c6ca9e14d81
