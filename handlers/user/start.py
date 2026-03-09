from aiogram import types

from keyboards.reply import main_menu
from loader import db, dp, config


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    await db.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    text = (
        f"<b>{config.shop_title}</b>\n\n"
        "Добро пожаловать в магазин-бот.\n"
        "Используй кнопки ниже: каталог, корзина, баланс и заказы."
    )
    await message.answer(text, reply_markup=main_menu())
