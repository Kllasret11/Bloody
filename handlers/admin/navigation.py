from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.reply import back_menu, main_menu
from loader import dp
from .panel import admin_panel_keyboard


ADMIN_STATES = {
    "AddAdminState:waiting_for_user_id",
    "BalanceState:waiting_for_user_id",
    "BalanceState:waiting_for_amount",
    "BroadcastState:waiting_for_message",
    "PromoCreateState:waiting_for_code",
    "PromoCreateState:waiting_for_percent",
    "ProductCreateState:waiting_for_name",
    "ProductCreateState:waiting_for_description",
    "ProductCreateState:waiting_for_price",
    "ProductCreateState:waiting_for_stock",
}

USER_STATES = {
    "CheckoutState:waiting_for_phone",
    "CheckoutState:waiting_for_delivery_method",
    "CheckoutState:waiting_for_location",
    "CheckoutState:waiting_for_address",
    "CheckoutState:waiting_for_promo",
    "SosState:waiting_for_message",
}


@dp.message_handler(lambda m: (m.text or '').strip() == "⬅ Назад", state="*")
async def universal_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await message.answer("Ты уже в меню.", reply_markup=main_menu())
        return

    await state.finish()

    if current_state in ADMIN_STATES:
        await message.answer("↩️ Возврат в админ панель.", reply_markup=admin_panel_keyboard())
        return

    if current_state in USER_STATES:
        await message.answer("↩️ Возврат в главное меню.", reply_markup=main_menu())
        return

    await message.answer("↩️ Действие отменено.", reply_markup=main_menu())
