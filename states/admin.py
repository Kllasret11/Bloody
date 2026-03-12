from aiogram.dispatcher.filters.state import State, StatesGroup


class ProductCreateState(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_stock = State()
    waiting_for_photo = State()


class CategoryState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_edit_name = State()


class AddBalanceState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()


class AdminReplySosState(StatesGroup):
    waiting_for_ticket_id = State()
    waiting_for_reply = State()


class FindUserState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_reply = State()
