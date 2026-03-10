from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.inline import cart_item_kb, checkout_kb
from keyboards.reply import (
    contact_request_menu,
    delivery_method_menu,
    location_request_menu,
    main_menu,
    remove_keyboard,
)
from loader import db, dp
from states import CheckoutState


def _delivery_text(address=None, latitude=None, longitude=None):
    if address:
        return address
    if latitude is not None and longitude is not None:
        return f"Геопозиция: {latitude:.6f}, {longitude:.6f}"
    return "-"


@dp.message_handler(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    cart_items = await db.get_cart(message.from_user.id)

    if not cart_items:
        await message.answer("Корзина пуста.")
        return

    total = 0.0

    for item in cart_items:
        price = float(item.get("price", 0))
        qty = int(item.get("quantity", 1))
        item_total = price * qty
        total += item_total

        text = (
            f"<b>{item.get('name', 'Товар')}</b>\n"
            f"💰 Цена: {price:.2f}\n"
            f"🔢 Количество: {qty}\n"
            f"🧾 Сумма: {item_total:.2f}"
        )

        product_id = item.get("product_id")

        if product_id:
            await message.answer(
                text,
                reply_markup=cart_item_kb(int(product_id))
            )
        else:
            await message.answer(text)

    await message.answer(
        f"<b>Итого:</b> {total:.2f}",
        reply_markup=checkout_kb()
    )


@dp.callback_query_handler(lambda c: c.data.startswith("cartdel:"))
async def remove_cart_item(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])

    await db.remove_cart_item(product_id, call.from_user.id)

    await call.answer("Товар удалён из корзины")

    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass


@dp.callback_query_handler(lambda c: c.data == "checkout")
async def start_checkout(call: types.CallbackQuery, state: FSMContext):
    cart_items = await db.get_cart(call.from_user.id)

    if not cart_items:
        await call.answer("Корзина пуста.", show_alert=True)
        return

    await state.finish()
    await CheckoutState.waiting_for_phone.set()

    await call.message.answer(
        "Нажми кнопку ниже, чтобы отправить номер телефона.",
        reply_markup=contact_request_menu()
    )

    await call.answer()


@dp.message_handler(content_types=types.ContentType.CONTACT, state=CheckoutState.waiting_for_phone)
async def checkout_phone_contact(message: types.Message, state: FSMContext):
    contact = message.contact

    if not contact:
        await message.answer("Не удалось получить контакт.")
        return

    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer("Отправь свой номер телефона.")
        return

    await state.update_data(phone=contact.phone_number)
    await CheckoutState.waiting_for_delivery_method.set()

    await message.answer(
        "Как указать адрес доставки?",
        reply_markup=delivery_method_menu()
    )


@dp.message_handler(state=CheckoutState.waiting_for_phone)
async def checkout_phone_invalid(message: types.Message):
    await message.answer(
        "Нужно отправить номер через кнопку ниже.",
        reply_markup=contact_request_menu()
    )


@dp.message_handler(lambda m: m.text == "✍️ Ввести адрес вручную", state=CheckoutState.waiting_for_delivery_method)
@dp.message_handler(lambda m: m.text == "✍️ Ввести адрес вручную", state=CheckoutState.waiting_for_location)
async def checkout_manual_address(message: types.Message):
    await CheckoutState.waiting_for_address.set()

    await message.answer(
        "Введите адрес доставки:",
        reply_markup=remove_keyboard()
    )


@dp.message_handler(lambda m: m.text == "📍 Отправить геопозицию", state=CheckoutState.waiting_for_delivery_method)
async def checkout_request_location(message: types.Message):
    await CheckoutState.waiting_for_location.set()

    await message.answer(
        "Отправьте геопозицию доставки.",
        reply_markup=location_request_menu()
    )


@dp.message_handler(content_types=types.ContentType.LOCATION, state=CheckoutState.waiting_for_location)
async def checkout_location(message: types.Message, state: FSMContext):
    location = message.location
    data = await state.get_data()

    try:
        order_id = await db.create_order_from_cart(
            user_id=message.from_user.id,
            phone=data["phone"],
            latitude=location.latitude,
            longitude=location.longitude
        )
    except ValueError:
        await state.finish()
        await message.answer(
            "Корзина пуста.",
            reply_markup=main_menu()
        )
        return
    except RuntimeError as exc:
        await state.finish()
        if str(exc) == "INSUFFICIENT_FUNDS":
            await message.answer(
                "Недостаточно средств на балансе.",
                reply_markup=main_menu()
            )
            return
        raise

    await state.finish()

    await message.answer(
        f"Заказ №{order_id} оформлен.\n"
        f"📍 {_delivery_text(None, location.latitude, location.longitude)}\n"
        f"📞 {data['phone']}",
        reply_markup=main_menu()
    )


@dp.message_handler(state=CheckoutState.waiting_for_location)
async def checkout_location_invalid(message: types.Message):
    await message.answer(
        "Отправьте геопозицию кнопкой ниже или выберите ввод адреса вручную.",
        reply_markup=location_request_menu()
    )


@dp.message_handler(state=CheckoutState.waiting_for_address)
async def checkout_address(message: types.Message, state: FSMContext):
    address = message.text.strip()

    if len(address) < 5:
        await message.answer("Адрес слишком короткий.")
        return

    data = await state.get_data()

    try:
        order_id = await db.create_order_from_cart(
            user_id=message.from_user.id,
            phone=data["phone"],
            address=address
        )
    except ValueError:
        await state.finish()
        await message.answer(
            "Корзина пуста.",
            reply_markup=main_menu()
        )
        return
    except RuntimeError as exc:
        await state.finish()
        if str(exc) == "INSUFFICIENT_FUNDS":
            await message.answer(
                "Недостаточно средств на балансе.",
                reply_markup=main_menu()
            )
            return
        raise

    await state.finish()

    await message.answer(
        f"Заказ №{order_id} оформлен.\n"
        f"📍 {address}\n"
        f"📞 {data['phone']}",
        reply_markup=main_menu()
    )