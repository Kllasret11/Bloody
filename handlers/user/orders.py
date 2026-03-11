from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.inline import reorder_kb
from keyboards.reply import main_menu
from loader import config, db, dp, bot
from states import SosState
from utils.cooldown import hit


STATUS_LABELS = {
    "new": "новый",
    "processing": "в обработке",
    "delivering": "доставляется",
    "completed": "завершён",
    "cancelled": "отменён",
    "paid": "оплачен",
}


def _status_label(status: str) -> str:
    status = (status or "").strip().lower()
    return STATUS_LABELS.get(status, status or "-")


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

    await message.answer("<b>Мои заказы</b>")
    for order in orders[:20]:
        text = (
            f"№{order['id']} — {float(order['total_amount']):.2f} — {_status_label(str(order['status']))}\n"
            f"📍 {_order_delivery(order)}\n"
            f"📞 {order['phone'] or '-'}"
        )
        await message.answer(text, reply_markup=reorder_kb(int(order["id"])))


@dp.callback_query_handler(lambda c: c.data.startswith("reorder:"))
async def reorder(call: types.CallbackQuery) -> None:
    if not hit(call.from_user.id, "reorder", 1.0):
        await call.answer("Слишком часто.", show_alert=False)
        return
    order_id = int(call.data.split(":")[1])
    items = await db.get_order_items(order_id)
    if not items:
        await call.answer("Не удалось найти позиции заказа.", show_alert=True)
        return

    added = 0
    missing = []
    for item in items:
        product_id = item["product_id"]
        if product_id is None:
            missing.append(str(item["product_name"]))
            continue

        product = await db.get_product_available(int(product_id))
        if not product:
            missing.append(str(item["product_name"]))
            continue

        qty = int(item["quantity"])
        await db.add_to_cart(call.from_user.id, int(product_id), qty)
        added += 1

    if added == 0:
        await call.answer("Товары из заказа сейчас недоступны.", show_alert=True)
        return

    text = f"Добавил в корзину позиций: <b>{added}</b>."
    if missing:
        text += "\n\nНе в наличии:\n" + "\n".join(f"- {name}" for name in missing[:15])
        if len(missing) > 15:
            text += f"\n…и ещё {len(missing) - 15}"

    await call.message.answer(text, reply_markup=main_menu())
    await call.answer()


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