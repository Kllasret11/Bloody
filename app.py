from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.inline import reorder_kb
from keyboards.reply import main_menu
from loader import config, db, dp, bot
from states import SosState
from utils.cooldown import hit


STATUS_LABELS = {
    "new": "🆕 Новый",
    "processing": "✅ Подтверждён",
    "confirmed": "✅ Подтверждён",
    "cooking": "👨‍🍳 В работе",
    "preparing": "👨‍🍳 В работе",
    "delivery": "🚚 В пути",
    "delivering": "🚚 В пути",
    "completed": "✨ Завершён",
    "done": "✨ Завершён",
    "cancelled": "❌ Отменён",
    "paid": "💳 Оплачен",
}


def _status_label(status: str) -> str:
    status = (status or "").strip().lower()
    return STATUS_LABELS.get(status, status or "—")


def _order_delivery(order) -> str:
    if order["address"]:
        return str(order["address"])

    latitude = order["latitude"]
    longitude = order["longitude"]

    if latitude is not None and longitude is not None:
        return f"Геопозиция: {float(latitude):.6f}, {float(longitude):.6f}"

    return "—"


def _short_items_text(items) -> str:
    if not items:
        return "—"

    names = [str(item["product_name"]) for item in items if item["product_name"]]
    if not names:
        return "—"

    if len(names) == 1:
        return names[0]

    return f"{names[0]}, +{len(names) - 1}"


def _full_items_text(items) -> str:
    if not items:
        return "• Нет данных"

    lines = []
    for item in items:
        name = str(item["product_name"])
        qty = int(item["quantity"])
        price = float(item["price"])
        lines.append(f"• {name} — {qty} шт. × {price:.2f}")

    return "\n".join(lines)


@dp.message_handler(lambda m: m.text == "📦 Мои заказы")
async def my_orders(message: types.Message) -> None:
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer("У тебя пока нет заказов.", reply_markup=main_menu())
        return

    await message.answer("<b>📦 Мои заказы</b>")

    for order in orders[:20]:
        items = await db.get_order_items(int(order["id"]))

        text = (
            f"<b>📦 Заказ №{order['id']}</b>\n"
            f"🛍 Товары: {_short_items_text(items)}\n"
            f"💰 Сумма: <b>{float(order['total_amount']):.2f}</b>\n"
            f"📌 Статус: <b>{_status_label(str(order['status']))}</b>\n"
            f"📍 Доставка: {_order_delivery(order)}\n"
            f"📞 Телефон: {order['phone'] or '—'}"
        )

        await message.answer(
            text,
            reply_markup=reorder_kb(int(order["id"]))
        )


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

    text = f"🛒 Добавил в корзину позиций: <b>{added}</b>."
    if missing:
        text += "\n\n❌ Сейчас недоступны:\n" + "\n".join(f"• {name}" for name in missing[:15])
        if len(missing) > 15:
            text += f"\n…и ещё {len(missing) - 15}"

    await call.message.answer(text, reply_markup=main_menu())
    await call.answer("Готово")


@dp.message_handler(commands=["orderinfo"])
async def order_info_command(message: types.Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Используй: /orderinfo ID_ЗАКАЗА")
        return

    order_id = int(parts[1])
    order = await db.get_order(order_id)

    if not order or int(order["user_id"]) != message.from_user.id:
        await message.answer("Заказ не найден.")
        return

    items = await db.get_order_items(order_id)

    text = (
        f"<b>📦 Заказ №{order_id}</b>\n\n"
        f"🛍 <b>Состав заказа:</b>\n{_full_items_text(items)}\n\n"
        f"💰 <b>Итого:</b> {float(order['total_amount']):.2f}\n"
        f"📌 <b>Статус:</b> {_status_label(str(order['status']))}\n"
        f"📍 <b>Доставка:</b> {_order_delivery(order)}\n"
        f"📞 <b>Телефон:</b> {order['phone'] or '—'}"
    )

    await message.answer(text, reply_markup=reorder_kb(order_id))


@dp.message_handler(commands=["sos"])
@dp.message_handler(lambda m: m.text == "🆘 SOS")
async def sos_start(message: types.Message, state: FSMContext) -> None:
    await SosState.waiting_for_message.set()
    await message.answer("Опиши проблему одним сообщением:")


@dp.message_handler(state=SosState.waiting_for_message)
async def sos_finish(message: types.Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Сообщение пустое. Опиши проблему одним сообщением.")
        return

    ticket_id = await db.create_support_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        message=text,
    )

    await state.finish()

    await message.answer(
        f"✅ Обращение №{ticket_id} отправлено администраторам.",
        reply_markup=main_menu()
    )

    admins = getattr(config, "admins", [])

    notify_text = (
        f"🆘 <b>Новое SOS обращение</b>\n"
        f"🆔 ID обращения: <code>{ticket_id}</code>\n"
        f"👤 Пользователь: {message.from_user.full_name}\n"
        f"🔹 Username: @{message.from_user.username}" if message.from_user.username else
        f"🆘 <b>Новое SOS обращение</b>\n"
        f"🆔 ID обращения: <code>{ticket_id}</code>\n"
        f"👤 Пользователь: {message.from_user.full_name}\n"
    )

    notify_text += (
        f"\n🪪 User ID: <code>{message.from_user.id}</code>\n\n"
        f"{text}"
    )

    for admin_id in admins:
        try:
            await bot.send_message(admin_id, notify_text)
        except Exception:
            continue