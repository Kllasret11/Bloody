from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import main_menu
from loader import config, db, dp, bot
from states import SosState


def _order_delivery(order) -> str:
    if order["address"]:
        return str(order["address"])

    latitude = order["latitude"]
    longitude = order["longitude"]

    if latitude is not None and longitude is not None:
        return f"Геопозиция: {float(latitude):.6f}, {float(longitude):.6f}"

    return "-"


@dp.message_handler(lambda m: m.text == "📦 Мои заказы")
async def my_orders(message: types.Message) -> None:
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer("У тебя пока нет заказов.")
        return

    lines = ["<b>Мои заказы</b>"]

    for order in orders[:20]:
        lines.append(
            f"№{order['id']} — {float(order['total_amount']):.2f} — {order['status']}\n"
            f"📍 {_order_delivery(order)}\n"
            f"📞 {order['phone'] or '-'}"
        )

    await message.answer("\n\n".join(lines))


@dp.message_handler(commands=["sos"])
@dp.message_handler(lambda m: m.text == "🆘 SOS")
async def sos_start(message: types.Message, state: FSMContext) -> None:
    await SosState.waiting_for_message.set()
    await message.answer("Опиши проблему одним сообщением:")


@dp.message_handler(state=SosState.waiting_for_message)
async def sos_finish(message: types.Message, state: FSMContext) -> None:
    ticket_id = await db.create_support_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        message=message.text.strip(),
    )

    await state.finish()

    await message.answer(
        f"Обращение №{ticket_id} отправлено администраторам.",
        reply_markup=main_menu()
    )

    admins = config.admins

    notify_text = (
        f"🆘 <b>Новое SOS обращение</b>\n"
        f"ID обращения: <code>{ticket_id}</code>\n"
        f"Пользователь: {message.from_user.full_name}\n"
        f"User ID: <code>{message.from_user.id}</code>\n\n"
        f"{message.text.strip()}"
    )

    for admin_id in admins:
        try:
            await bot.send_message(admin_id, notify_text)
        except Exception:
            continue