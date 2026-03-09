from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminAuthState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()


class AddCategoryState(StatesGroup):
    waiting_for_name = State()


class AddProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_category = State()


class EditPriceState(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_new_price = State()


class AddBalanceState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
