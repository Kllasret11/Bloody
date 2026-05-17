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
from loader import bot, config, db, dp
from states import CheckoutState


def _delivery_text(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    if address:
        return address
    if latitude is not None and longitude is not None:
        return f"Геопозиция: {latitude:.6f}, {longitude:.6f}"
    return "-"


async def _notify_admins_about_order(
    user: types.User,
    order_id: int,
    phone: str,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> None:
    delivery = _delivery_text(address=address, latitude=latitude, longitude=longitude)

    text = (
        "<b>🆕 Новый заказ</b>\n\n"
        f"📦 Заказ: <b>№{order_id}</b>\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📞 Телефон: {phone}\n"
        f"📍 Доставка: {delivery}"
    )

    for admin_id in config.admins:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass


@dp.message_handler(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message) -> None:
    cart_items = await db.get_cart(message.from_user.id)

    if not cart_items:
        await message.answer("Корзина пуста.")
        return

    total = 0.0
    for item in cart_items:
        price = float(item["price"])
        qty = int(item["quantity"])
        item_total = price * qty
        total += item_total

        text = (
            f"<b>{item['name']}</b>\n"
            f"💰 Цена: {price:.2f}\n"
            f"🔢 Количество: {qty}\n"
            f"🧾 Сумма: {item_total:.2f}"
        )
        await message.answer(
            text,
            reply_markup=cart_item_kb(int(item["product_id"])),
        )

    await message.answer(
        f"<b>Итого:</b> {total:.2f}",
        reply_markup=checkout_kb(),
    )


@dp.callback_query_handler(lambda c: c.data.startswith("cartdel:"))
async def remove_cart_item(call: types.CallbackQuery) -> None:
    product_id = int(call.data.split(":")[1])
    await db.remove_cart_item(product_id, call.from_user.id)
    await call.answer("Товар удалён из корзины")

    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass


@dp.callback_query_handler(lambda c: c.data == "checkout")
async def start_checkout(call: types.CallbackQuery, state: FSMContext) -> None:
    cart_items = await db.get_cart(call.from_user.id)
    if not cart_items:
        await call.answer("Корзина пуста.", show_alert=True)
        return

    await state.finish()
    await CheckoutState.waiting_for_phone.set()
    await call.message.answer(
        "Нажми кнопку ниже, чтобы отправить номер телефона.",
        reply_markup=contact_request_menu(),
    )
    await call.answer()


@dp.message_handler(
    content_types=types.ContentType.CONTACT,
    state=CheckoutState.waiting_for_phone,
)
async def checkout_phone_contact(message: types.Message, state: FSMContext) -> None:
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
        reply_markup=delivery_method_menu(),
    )


@dp.message_handler(state=CheckoutState.waiting_for_phone)
async def checkout_phone_invalid(message: types.Message) -> None:
    await message.answer(
        "Нужно отправить номер через кнопку ниже.",
        reply_markup=contact_request_menu(),
    )


@dp.message_handler(
    lambda m: m.text == "✍️ Ввести адрес вручную",
    state=CheckoutState.waiting_for_delivery_method,
)
@dp.message_handler(
    lambda m: m.text == "✍️ Ввести адрес вручную",
    state=CheckoutState.waiting_for_location,
)
async def checkout_manual_address(message: types.Message) -> None:
    await CheckoutState.waiting_for_address.set()
    await message.answer(
        "Введите адрес доставки:",
        reply_markup=remove_keyboard(),
    )


@dp.message_handler(
    lambda m: m.text == "📍 Отправить геопозицию",
    state=CheckoutState.waiting_for_delivery_method,
)
async def checkout_request_location(message: types.Message) -> None:
    await CheckoutState.waiting_for_location.set()
    await message.answer(
        "Отправьте геопозицию доставки.",
        reply_markup=location_request_menu(),
    )


@dp.message_handler(
    content_types=types.ContentType.LOCATION,
    state=CheckoutState.waiting_for_location,
)
async def checkout_location(message: types.Message, state: FSMContext) -> None:
    location = message.location
    await state.update_data(latitude=location.latitude, longitude=location.longitude, address=None)
    
    from keyboards.reply import skip_menu
    await CheckoutState.waiting_for_promo.set()
    await message.answer(
        "🏷️ <b>Промокод</b>\n\n"
        "Введите промокод (если есть) или нажмите кнопку <b>Пропустить</b> ниже:",
        parse_mode="HTML",
        reply_markup=skip_menu(),
    )


@dp.message_handler(state=CheckoutState.waiting_for_location)
async def checkout_location_invalid(message: types.Message) -> None:
    await message.answer(
        "Отправь геопозицию через кнопку ниже или выбери ручной ввод адреса.",
        reply_markup=location_request_menu(),
    )


@dp.message_handler(state=CheckoutState.waiting_for_address)
async def checkout_address(message: types.Message, state: FSMContext) -> None:
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("Адрес слишком короткий. Введи адрес подробнее.")
        return

    await state.update_data(address=address, latitude=None, longitude=None)
    
    from keyboards.reply import skip_menu
    await CheckoutState.waiting_for_promo.set()
    await message.answer(
        "🏷️ <b>Промокод</b>\n\n"
        "Введите промокод (если есть) или нажмите кнопку <b>Пропустить</b> ниже:",
        parse_mode="HTML",
        reply_markup=skip_menu(),
    )


@dp.message_handler(state=CheckoutState.waiting_for_promo)
async def checkout_promo(message: types.Message, state: FSMContext) -> None:
    code = message.text.strip()
    promo_code = None

    if code != "Пропустить" and code != "/skip":
        promo = await db.get_promo(code)
        if not promo:
            await message.answer(
                "❌ Неверный или истекший промокод. Попробуйте еще раз или нажмите кнопку <b>Пропустить</b>:",
                parse_mode="HTML",
            )
            return
        
        cart_items = await db.get_cart(message.from_user.id)
        total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)
        if promo.get("min_order_amount") and total_amount < float(promo["min_order_amount"]):
            await message.answer(
                f"❌ Этот промокод можно применить только к заказам от {float(promo['min_order_amount']):.2f} руб.\n"
                f"Сумма вашей корзины: {total_amount:.2f} руб.\n"
                "Попробуйте другой промокод или нажмите <b>Пропустить</b>:",
                parse_mode="HTML",
            )
            return

        promo_code = str(promo["code"])
        await message.answer(
            f"✅ Промокод <b>{promo_code}</b> успешно применён! Скидка: {int(promo['percent'])}%.",
            parse_mode="HTML",
        )

    data = await state.get_data()
    phone = data["phone"]
    address = data.get("address")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    try:
        order_id = await db.create_order_from_cart(
            user_id=message.from_user.id,
            phone=phone,
            address=address,
            latitude=latitude,
            longitude=longitude,
            promo_code=promo_code,
        )
    except ValueError:
        await state.finish()
        await message.answer("Корзина пуста.", reply_markup=main_menu())
        return
    except RuntimeError as exc:
        if str(exc) == "INSUFFICIENT_FUNDS":
            await state.finish()
            await message.answer(
                "Недостаточно средств на балансе.",
                reply_markup=main_menu(),
            )
            return
        elif str(exc) == "OUT_OF_STOCK":
            await state.finish()
            await message.answer(
                "К сожалению, некоторые товары закончились на складе.",
                reply_markup=main_menu(),
            )
            return
        raise

    await _notify_admins_about_order(
        user=message.from_user,
        order_id=order_id,
        phone=phone,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    await state.finish()
    
    orders = await db.get_user_orders(message.from_user.id)
    order_detail = next((o for o in orders if o["id"] == order_id), None)
    
    confirm_text = f"✅ Заказ №{order_id} оформлен.\n"
    if order_detail:
        confirm_text += f"💰 Итоговая сумма к оплате (с учетом скидок): <b>{float(order_detail['total_amount']):.2f} руб.</b>\n"
    confirm_text += f"📍 {_delivery_text(address=address, latitude=latitude, longitude=longitude)}"

    await message.answer(
        confirm_text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )