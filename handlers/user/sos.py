from aiogram import types

from keyboards.reply import main_menu
from loader import bot, config, db, dp


async def _notify_admins_about_sos(
    user: types.User,
    ticket_id: int,
    text: str,
) -> None:
    msg = (
        "<b>🆘 Новое SOS обращение</b>\n\n"
        f"📝 ID обращения: <b>{ticket_id}</b>\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📨 Сообщение:\n{text}"
    )

    for admin_id in config.admins:
        try:
            await bot.send_message(admin_id, msg)
        except Exception:
            pass


@dp.message_handler(commands=["sos"])
@dp.message_handler(lambda m: m.text == "🆘 SOS")
async def send_sos_request(message: types.Message) -> None:
    await message.answer(
        "Напиши сообщение одним сообщением:\n\n"
        "Например: проблема с заказом, не пришёл товар, ошибка оплаты."
    )


@dp.message_handler(
    lambda m: m.reply_to_message and m.reply_to_message.text and "Напиши сообщение одним сообщением" in m.reply_to_message.text
)
async def save_sos_request(message: types.Message) -> None:
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Сообщение слишком короткое.", reply_markup=main_menu())
        return

    ticket_id = await db.create_support_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        message=text,
    )

    await _notify_admins_about_sos(
        user=message.from_user,
        ticket_id=ticket_id,
        text=text,
    )

    await message.answer(
        f"✅ Обращение отправлено. Номер: #{ticket_id}",
        reply_markup=main_menu(),
    )