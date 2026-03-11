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
from utils.cooldown import hit


def _delivery_text(address: str | None = None, latitude: float | None = None, longitude: float | None = None) -> str:
    if address:
        return address
    if latitude is not None and longitude is not None:
        return f"Геопозиция: {latitude:.6f}, {longitude:.6f}"
    return "-"


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
        await message.answer(text, reply_markup=cart_item_kb(int(item["product_id"])))

    await message.answer(f"<b>Итого:</b> {total:.2f}", reply_markup=checkout_kb())


@dp.callback_query_handler(lambda c: c.data.startswith("cartdel:"))
async def remove_cart_item(call: types.CallbackQuery) -> None:

    if not hit(call.from_user.id, "cartdel", 0.5):
        await call.answer("Слишком часто.", show_alert=False)
        return


    product_id = int(call.data.split(":")[1])
    await db.remove_cart_item(product_id, call.from_user.id)
    await call.answer("Товар удалён из корзины")
    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass


@dp.callback_query_handler(lambda c: c.data == "checkout")
async def start_checkout(call: types.CallbackQuery, state: FSMContext) -> None:

    if not hit(call.from_user.id, "checkout", 1.0):
        await call.answer("Слишком часто.", show_alert=False)
        return


    cart_items = await db.get_cart(call.from_user.id)
    if not cart_items:
        await call.answer("Корзина пуста.", show_alert=True)
        return

    # Preserve promo_code (if user entered it earlier)
    old_data = await state.get_data()
    promo_code = old_data.get("promo_code")
    await state.finish()
    if promo_code:
        await state.update_data(promo_code=promo_code)
    await CheckoutState.waiting_for_phone.set()
    await call.message.answer(
        "Нажми кнопку ниже, чтобы отправить номер телефона.",
        reply_markup=contact_request_menu(),
    )
    await call.answer()



@dp.callback_query_handler(lambda c: c.data == "promo")
async def start_promo(call: types.CallbackQuery, state: FSMContext) -> None:
    if not hit(call.from_user.id, "promo", 1.0):
        await call.answer("Слишком часто.", show_alert=False)
        return
    await CheckoutState.waiting_for_promo.set()
    await call.message.answer("Введи промокод одним сообщением:")
    await call.answer()


@dp.message_handler(state=CheckoutState.waiting_for_promo)
async def promo_input(message: types.Message, state: FSMContext) -> None:
    code = (message.text or "").strip().upper()
    if not code or len(code) < 3:
        await message.answer("Промокод слишком короткий. Попробуй ещё раз.")
        return

    promo = await db.get_promo(code)
    if not promo:
        await message.answer("Промокод не найден или недействителен.")
        await state.set_state(None)
        return

    await state.update_data(promo_code=str(promo["code"]))
    await state.set_state(None)
    await message.answer(f"Промокод <b>{promo['code']}</b> применён: скидка {int(promo['percent'])}%.")




@dp.message_handler(content_types=types.ContentType.CONTACT, state=CheckoutState.waiting_for_phone)
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
    await message.answer("Как указать адрес доставки?", reply_markup=delivery_method_menu())


@dp.message_handler(state=CheckoutState.waiting_for_phone)
async def checkout_phone_invalid(message: types.Message) -> None:
    await message.answer(
        "Нужно отправить номер через кнопку ниже.",
        reply_markup=contact_request_menu(),
    )


@dp.message_handler(lambda m: m.text == "✍️ Ввести адрес вручную", state=CheckoutState.waiting_for_delivery_method)
@dp.message_handler(lambda m: m.text == "✍️ Ввести адрес вручную", state=CheckoutState.waiting_for_location)
async def checkout_manual_address(message: types.Message) -> None:
    await CheckoutState.waiting_for_address.set()
    await message.answer("Введите адрес доставки:", reply_markup=remove_keyboard())


@dp.message_handler(lambda m: m.text == "📍 Отправить геопозицию", state=CheckoutState.waiting_for_delivery_method)
async def checkout_request_location(message: types.Message) -> None:
    await CheckoutState.waiting_for_location.set()
    await message.answer("Отправьте геопозицию доставки.", reply_markup=location_request_menu())


@dp.message_handler(content_types=types.ContentType.LOCATION, state=CheckoutState.waiting_for_location)
async def checkout_location(message: types.Message, state: FSMContext) -> None:
    location = message.location
    data = await state.get_data()

    try:
        promo_code = data.get("promo_code")
        order_id = await db.create_order_from_cart(
            user_id=message.from_user.id,
            phone=data["phone"],
            latitude=location.latitude,
            longitude=location.longitude,

            promo_code=promo_code,


        )
    except ValueError:
        await state.finish()
        await message.answer("Корзина пуста.", reply_markup=main_menu())
        return
    except RuntimeError as exc:
        if str(exc) == "INSUFFICIENT_FUNDS":
            await message.answer("Недостаточно средств на балансе.", reply_markup=main_menu())
            await state.finish()

            return
        if str(exc) == "OUT_OF_STOCK":
            await message.answer(
                "Некоторые товары закончились на складе. Проверь корзину и попробуй снова.",
                reply_markup=main_menu(),
            )
            await state.finish()


            return
        raise

    await state.finish()
    await message.answer(
        f"✅ Заказ №{order_id} оформлен.\n📍 {_delivery_text(latitude=location.latitude, longitude=location.longitude)}",
        reply_markup=main_menu(),
    )
    notify_text = (
        f"📦 <b>Новый заказ</b>\n"
        f"№<code>{order_id}</code>\n"
        f"User ID: <code>{message.from_user.id}</code>\n"
        f"📞 {data.get('phone')}\n"
        f"📍 {_delivery_text(latitude=location.latitude, longitude=location.longitude)}\n"
        f"Статус: <b>в обработке</b>"
    )
    for admin_id in config.admins:
        try:
            await bot.send_message(admin_id, notify_text)
        except Exception:
            continue


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

    data = await state.get_data()
    try:
        promo_code = data.get("promo_code")
        order_id = await db.create_order_from_cart(
            user_id=message.from_user.id,
            phone=data["phone"],
            address=address,

            promo_code=promo_code,


        )
    except ValueError:
        await state.finish()
        await message.answer("Корзина пуста.", reply_markup=main_menu())
        return
    except RuntimeError as exc:
        if str(exc) == "INSUFFICIENT_FUNDS":
            await message.answer("Недостаточно средств на балансе.", reply_markup=main_menu())
            await state.finish()

            return
        if str(exc) == "OUT_OF_STOCK":
            await message.answer(
                "Некоторые товары закончились на складе. Проверь корзину и попробуй снова.",
                reply_markup=main_menu(),
            )
            await state.finish()


            return
        raise

    await state.finish()
    await message.answer(
        f"✅ Заказ №{order_id} оформлен.\n📍 {_delivery_text(address=address)}",
        reply_markup=main_menu(),

    )
    notify_text = (
        f"📦 <b>Новый заказ</b>\n"
        f"№<code>{order_id}</code>\n"
        f"User ID: <code>{message.from_user.id}</code>\n"
        f"📞 {data.get('phone')}\n"
        f"📍 {_delivery_text(address=address)}\n"
        f"Статус: <b>в обработке</b>"
    )
    for admin_id in config.admins:
        try:
            await bot.send_message(admin_id, notify_text)
        except Exception:
            continue

