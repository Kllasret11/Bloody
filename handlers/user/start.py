from aiogram import types

from keyboards.reply import main_menu
from loader import db, dp

WELCOME_TEXT = (
    "Привет! 👋\n\n"
    "🤖 Я бот-магазин по продаже товаров любой категории.\n\n"
    "🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся товары воспользуйтесь командой /menu.\n\n"
    "💰 Пополнить счет можно через Каспи или Qiwi.\n\n"
    "❓ Возникли вопросы? Не проблема! Команда /sos поможет связаться с админами, которые постараются как можно быстрее откликнуться.\n\n"
    "🤝 Нашли проблему? Свяжитесь с разработчиком Yan Krivolapov"
)


async def _ensure_user(message: types.Message) -> None:
    await db.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    await _ensure_user(message)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@dp.message_handler(commands=["menu"])
async def cmd_menu(message: types.Message) -> None:
    await _ensure_user(message)
    await message.answer("Открываю меню магазина.", reply_markup=main_menu())
