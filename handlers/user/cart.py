from aiogram import types

from keyboards.inline import cart_kb
from loader import db, dp


@dp.message_handler(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message) -> None:
    cart_items = await db.get_cart(message.from_user.id)
    if not cart_items:
        await message.answer("Корзина пуста.")
        return

    total = 0.0
    lines = ["<b>Корзина</b>"]
    for item in cart_items:
        item_total = float(item["price"]) * int(item["quantity"])
        total += item_total
        lines.append(f"• {item['name']} × {item['quantity']} = {item_total:.2f}")
    lines.append(f"\n<b>Итого:</b> {total:.2f}")
    await message.answer("\n".join(lines), reply_markup=cart_kb())


@dp.callback_query_handler(lambda c: c.data == "clearcart")
async def clear_cart(call: types.CallbackQuery) -> None:
    await db.clear_cart(call.from_user.id)
    await call.message.answer("Корзина очищена.")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery) -> None:
    try:
        order_id = await db.create_order_from_cart(call.from_user.id)
    except ValueError:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    except RuntimeError as exc:
        if str(exc) == "INSUFFICIENT_FUNDS":
            await call.answer("Недостаточно средств на балансе.", show_alert=True)
            return
        raise

    await call.message.answer(f"Заказ №{order_id} успешно оформлен и оплачен.")
    await call.answer()
