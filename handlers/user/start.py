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
    args = message.get_args()
    referrer_id = None
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.split("_")[1])
        except (ValueError, IndexError):
            pass

    is_new = await db.register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referrer_id=referrer_id,
    )

    if is_new and referrer_id:
        try:
            await message.bot.send_message(
                referrer_id,
                f"🎉 По твоей реферальной ссылке зарегистрировался новый пользователь: <b>{message.from_user.full_name}</b>!\n"
                f"💰 Тебе начислено <b>100.00</b> бонусов!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@dp.message_handler(commands=["menu"])
async def cmd_menu(message: types.Message) -> None:
    await db.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    await message.answer("Открываю меню магазина.", reply_markup=main_menu())
