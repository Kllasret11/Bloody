from aiogram.dispatcher.filters.state import State, StatesGroup


class CheckoutState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_delivery_method = State()
    waiting_for_location = State()
    waiting_for_address = State()
    waiting_for_promo = State()


class SosState(StatesGroup):
    waiting_for_message = State()
