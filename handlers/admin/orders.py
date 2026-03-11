from aiogram import types

from loader import dp, db, bot


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


ACTIVE_STATUSES = {"new", "processing", "confirmed", "cooking", "preparing", "delivery", "delivering"}
ARCHIVE_STATUSES = {"completed", "done", "cancelled"}


def _status_label(status: str) -> str:
    status = (status or "").strip().lower()
    return STATUS_LABELS.get(status, status or "—")


def _admin_orders_root_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🆕 Активные заказы", callback_data="admin_orders_active"))
    kb.add(types.InlineKeyboardButton("🕘 Архив заказов", callback_data="admin_orders_archive"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    return kb


def _order_card_keyboard(order_id: int, status: str) -> types.InlineKeyboardMarkup:
    status = (status or "").strip().lower()
    kb = types.InlineKeyboardMarkup(row_width=2)

    if status not in {"confirmed", "processing"}:
        kb.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_order_status:{order_id}:confirmed")
        )

    if status not in {"cooking", "preparing"}:
        kb.insert(
            types.InlineKeyboardButton("👨‍🍳 В работу", callback_data=f"admin_order_status:{order_id}:cooking")
        )

    if status not in {"delivery", "delivering"}:
        kb.add(
            types.InlineKeyboardButton("🚚 В пути", callback_data=f"admin_order_status:{order_id}:delivery")
        )

    if status not in {"completed", "done"}:
        kb.insert(
            types.InlineKeyboardButton("✨ Завершить", callback_data=f"admin_order_status:{order_id}:completed")
        )

    if status != "cancelled":
        kb.add(
            types.InlineKeyboardButton("❌ Отменить", callback_data=f"admin_order_status:{order_id}:cancelled")
        )

    if status in ARCHIVE_STATUSES:
        kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_orders_archive"))
    else:
        kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_orders_active"))

    return kb


def _orders_list_keyboard(orders, back_callback: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)

    for order in orders[:50]:
        kb.add(
            types.InlineKeyboardButton(
                text=f"📦 Заказ №{order['id']}",
                callback_data=f"admin_open_order:{order['id']}",
            )
        )

    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data=back_callback))
    return kb


def _items_short_text(items) -> str:
    if not items:
        return "—"

    names = [str(item["product_name"]) for item in items if item["product_name"]]
    if not names:
        return "—"

    if len(names) == 1:
        return names[0]

    return f"{names[0]}, +{len(names) - 1}"


def _items_full_text(items) -> str:
    if not items:
        return "• Нет данных"

    lines = []
    for item in items:
        name = str(item["product_name"])
        qty = int(item["quantity"])
        price = float(item["price"])
        lines.append(f"• {name} — {qty} шт. × {price:.2f}")

    return "\n".join(lines)


def _delivery_text(order) -> str:
    if order["address"]:
        return str(order["address"])

    latitude = order["latitude"]
    longitude = order["longitude"]

    if latitude is not None and longitude is not None:
        return f"{float(latitude):.6f}, {float(longitude):.6f}"

    return "—"


async def _build_order_text(order_id: int) -> tuple[str, str]:
    order = await db.get_order(order_id)
    if not order:
        return "❌ Заказ не найден.", "new"

    user = await db.get_user(int(order["user_id"]))
    items = await db.get_order_items(order_id)

    full_name = "Неизвестно"
    username = None

    if user:
        full_name = user["full_name"] or "Неизвестно"
        username = user["username"]

    username_text = f" (@{username})" if username else ""
    status = str(order["status"] or "new").lower()

    text = (
        f"<b>📦 Заказ №{order_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {full_name}{username_text}\n"
        f"🪪 <b>User ID:</b> <code>{order['user_id']}</code>\n"
        f"📞 <b>Телефон:</b> {order['phone'] or '—'}\n"
        f"📍 <b>Доставка:</b> {_delivery_text(order)}\n\n"
        f"🛍 <b>Состав заказа:</b>\n{_items_full_text(items)}\n\n"
        f"💰 <b>Итого:</b> {float(order['total_amount']):.2f}\n"
        f"📌 <b>Статус:</b> {_status_label(status)}"
    )
    return text, status


async def _show_orders_list(call: types.CallbackQuery, archive: bool = False):
    orders = await db.get_archive_orders() if archive else await db.get_active_orders()

    title = "🕘 <b>Архив заказов</b>" if archive else "🆕 <b>Активные заказы</b>"
    back_callback = "admin_orders"

    if not orders:
        await call.message.edit_text(
            f"{title}\n\nЗаказов пока нет.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("⬅ Назад", callback_data=back_callback)
            ),
        )
        await call.answer()
        return

    preview_lines = []
    for order in orders[:10]:
        items = await db.get_order_items(int(order["id"]))
        preview_lines.append(
            f"• №{order['id']} — {_items_short_text(items)} — {_status_label(str(order['status']))}"
        )

    text = f"{title}\n\n" + "\n".join(preview_lines)

    await call.message.edit_text(
        text,
        reply_markup=_orders_list_keyboard(orders, back_callback),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_orders")
async def admin_orders_root(call: types.CallbackQuery):
    await call.message.edit_text(
        "📦 <b>Управление заказами</b>",
        reply_markup=_admin_orders_root_keyboard(),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_orders_active")
async def admin_orders_active(call: types.CallbackQuery):
    await _show_orders_list(call, archive=False)


@dp.callback_query_handler(lambda c: c.data == "admin_orders_archive")
async def admin_orders_archive(call: types.CallbackQuery):
    await _show_orders_list(call, archive=True)


@dp.callback_query_handler(lambda c: c.data.startswith("admin_open_order:"))
async def admin_open_order(call: types.CallbackQuery):
    order_id = int(call.data.split(":")[1])

    text, status = await _build_order_text(order_id)

    await call.message.edit_text(
        text,
        reply_markup=_order_card_keyboard(order_id, status),
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_order_status:"))
async def admin_change_order_status(call: types.CallbackQuery):
    _, order_id_raw, new_status = call.data.split(":")
    order_id = int(order_id_raw)

    order = await db.get_order(order_id)
    if not order:
        await call.answer("Заказ не найден", show_alert=True)
        return

    await db.set_order_status(order_id, new_status, changed_by=call.from_user.id)

    updated_text, updated_status = await _build_order_text(order_id)

    await call.message.edit_text(
        updated_text,
        reply_markup=_order_card_keyboard(order_id, updated_status),
    )

    user_id = int(order["user_id"])
    try:
        await bot.send_message(
            user_id,
            (
                f"<b>📦 Обновление заказа №{order_id}</b>\n\n"
                f"📌 Новый статус: <b>{_status_label(new_status)}</b>"
            ),
        )
    except Exception:
        pass

    await call.answer("Статус обновлён")