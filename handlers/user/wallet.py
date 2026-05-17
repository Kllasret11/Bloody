import os
import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile, InlineKeyboardButton, InlineKeyboardMarkup

from loader import db, dp
from states import StatesGroup, State

# Global cache variables to prevent heavy network calls on every profile request
_bot_username = None
_profile_banner_file_id = None


class UserTopUpState(StatesGroup):
    waiting_for_amount = State()


def profile_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💳 Пополнить баланс (Тест)", callback_data="top_up_balance")
    )
    return kb


@dp.message_handler(commands=["profile"])
@dp.message_handler(lambda m: m.text == "👤 Профиль", state="*")
async def show_profile(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    
    # 1. Fetch main user details
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.register_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
        user = await db.get_user(message.from_user.id)

    # 2. Concurrently run DB queries to overlap latency
    referrals_count_task = db.get_referrals_count(message.from_user.id)
    orders_task = db.get_user_orders(message.from_user.id)
    
    referrals_count, orders = await asyncio.gather(referrals_count_task, orders_task)

    balance = float(user["balance"])
    referral_bonuses = float(user.get("referral_bonuses_earned", 0.0))
    orders_count = len(orders)

    # 3. Retrieve and cache the bot username to avoid slow Telegram API calls
    global _bot_username
    if not _bot_username:
        try:
            bot_user = await message.bot.get_me()
            _bot_username = bot_user.username
        except Exception:
            _bot_username = "bot"

    ref_link = f"https://t.me/{_bot_username}?start=ref_{message.from_user.id}"

    text = (
        "<b>👤 Профиль пользователя</b>\n\n"
        f"🧑 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"💰 Баланс: <b>{balance:.2f} руб.</b>\n"
        f"👥 Приглашено друзей: <b>{referrals_count}</b>\n"
        f"🎁 Бонусы за рефералов: <b>{referral_bonuses:.2f} руб.</b>\n"
        f"📦 Заказов оформлено: <b>{orders_count}</b>\n\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{ref_link}</code>"
    )

    # 4. Use cached file ID for the profile banner so it loads instantly without re-uploading
    global _profile_banner_file_id
    banner_path = "assets/profile_banner.png"
    if os.path.exists(banner_path):
        try:
            if _profile_banner_file_id:
                await message.answer_photo(photo=_profile_banner_file_id, caption=text, reply_markup=profile_kb(), parse_mode="HTML")
                return
            else:
                msg = await message.answer_photo(photo=InputFile(banner_path), caption=text, reply_markup=profile_kb(), parse_mode="HTML")
                if msg.photo:
                    _profile_banner_file_id = msg.photo[-1].file_id
                return
        except Exception:
            pass

    await message.answer(text, reply_markup=profile_kb(), parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data == "top_up_balance")
async def top_up_balance_callback(call: types.CallbackQuery) -> None:
    await UserTopUpState.waiting_for_amount.set()
    await call.message.answer(
        "💰 <b>Пополнение баланса (Тестирование)</b>\n\n"
        "Введите сумму в рублях для мгновенного пополнения баланса:",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message_handler(state=UserTopUpState.waiting_for_amount)
async def top_up_balance_amount(message: types.Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть положительным числом. Попробуйте еще раз:")
        return

    if amount <= 0:
        await message.answer("Сумма пополнения должна быть больше нуля. Попробуйте еще раз:")
        return

    await db.change_balance(message.from_user.id, amount)
    await state.finish()
    
    await message.answer(f"✅ Баланс успешно пополнен на <b>{amount:.2f} руб.</b>!", parse_mode="HTML")
    await show_profile(message, state)