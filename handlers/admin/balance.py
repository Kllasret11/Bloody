from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.database import Database

router = Router()

class BalanceState(StatesGroup):
user_id = State()
amount = State()
action = State()

@router.callback_query(F.data == "admin_balance")
async def balance_menu(callback: types.CallbackQuery):
keyboard = types.InlineKeyboardMarkup(
inline_keyboard=[
[types.InlineKeyboardButton(text="➕ Начислить баланс", callback_data="balance_add")],
[types.InlineKeyboardButton(text="➖ Списать баланс", callback_data="balance_remove")],
[types.InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")]
]
)

```
await callback.message.edit_text(
    "💰 Управление балансом",
    reply_markup=keyboard
)
```

@router.callback_query(F.data == "balance_add")
async def balance_add_start(callback: types.CallbackQuery, state: FSMContext):
await state.update_data(action="add")
await state.set_state(BalanceState.user_id)

```
await callback.message.edit_text(
    "Введите user_id пользователя\n\n"
    "Которому нужно начислить баланс"
)
```

@router.callback_query(F.data == "balance_remove")
async def balance_remove_start(callback: types.CallbackQuery, state: FSMContext):
await state.update_data(action="remove")
await state.set_state(BalanceState.user_id)

```
await callback.message.edit_text(
    "Введите user_id пользователя\n\n"
    "У которого нужно списать баланс"
)
```

@router.message(BalanceState.user_id)
async def balance_get_user(message: types.Message, state: FSMContext):
await state.update_data(user_id=int(message.text))
await state.set_state(BalanceState.amount)

```
await message.answer("Введите сумму")
```

@router.message(BalanceState.amount)
async def balance_apply(message: types.Message, state: FSMContext, db: Database):
data = await state.get_data()

```
user_id = data["user_id"]
action = data["action"]
amount = float(message.text)

if action == "remove":
    amount = -amount

await db.change_balance(user_id, amount)

await state.clear()

if amount > 0:
    text = f"✅ Баланс начислен\n\nUser ID: {user_id}\nСумма: +{amount}"
else:
    text = f"➖ Баланс списан\n\nUser ID: {user_id}\nСумма: {amount}"

await message.answer(text)
```
