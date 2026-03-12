from aiogram import types

from keyboards.reply import main_menu
from loader import db, dp
from services.referrals import parse_referral_payload

WELCOME_TEXT = (
    "Привет! 👋\n\n"
    "🤖 Я бот-магазин.\n\n"
    "🛍 Используй каталог, корзину и личный кабинет.\n"
    "👥 У тебя есть реферальная ссылка — зови друзей и получай бонусы.\n"
    "🆘 Если возникли вопросы — нажми SOS."
)


async def _ensure_user(message: types.Message) -> None:
    payload = parse_referral_payload(message.get_args()) if message.get_args() else None
    await db.upsert_user(
        user_id=int(message.from_user.id),
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referrer_id=payload,
    )


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    await _ensure_user(message)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@dp.message_handler(commands=["menu"])
async def cmd_menu(message: types.Message) -> None:
    await _ensure_user(message)
    await message.answer("Открываю меню магазина.", reply_markup=main_menu())
