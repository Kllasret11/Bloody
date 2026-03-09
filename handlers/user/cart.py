from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.inline import cart_kb
from loader import db, dp
from states import CheckoutState


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
async def checkout(call: types.CallbackQuery, state: FSMContext) -> None:
    cart_items = await db.get_cart(call.from_user.id)
    if not cart_items:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    await CheckoutState.waiting_for_address.set()
    await call.message.answer("Введи адрес доставки:")
    await call.answer()


@dp.message_handler(state=CheckoutState.waiting_for_address)
async def checkout_address(message: types.Message, state: FSMContext) -> None:
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("Адрес слишком короткий. Введи полный адрес.")
        return
    await state.update_data(address=address)
    await CheckoutState.waiting_for_phone.set()
    await message.answer("Введи номер телефона для связи:")


@dp.message_handler(state=CheckoutState.waiting_for_phone)
async def checkout_phone(message: types.Message, state: FSMContext) -> None:
    phone = message.text.strip()
    data = await state.get_data()
    try:
        order_id = await db.create_order_from_cart(message.from_user.id, data["address"], phone)
    except ValueError:
        await state.finish()
        await message.answer("Корзина пуста.")
        return
    except RuntimeError as exc:
        await state.finish()
        if str(exc) == "INSUFFICIENT_FUNDS":
            await message.answer("Недостаточно средств на балансе.")
            return
        raise

    await state.finish()
    await message.answer(f"Заказ №{order_id} успешно оформлен и оплачен.")
