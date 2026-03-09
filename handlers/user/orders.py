from aiogram import types

from loader import db, dp


@dp.message_handler(lambda m: m.text == "📦 Мои заказы")
async def my_orders(message: types.Message) -> None:
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У тебя пока нет заказов.")
        return

    lines = ["<b>Мои заказы</b>"]
    for order in orders[:20]:
        lines.append(
            f"№{order['id']} — {float(order['total_amount']):.2f} — {order['status']}"
        )
    await message.answer("\n".join(lines))
