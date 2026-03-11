from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import SUPER_ADMIN_ID
from utils.database import Database

router = Router()

class AddAdminState(StatesGroup):
user_id = State()

@router.callback_query(F.data == "admin_admins")
async def admins_menu(callback: types.CallbackQuery):
keyboard = types.InlineKeyboardMarkup(
inline_keyboard=[
[types.InlineKeyboardButton(text="➕ Добавить администратора", callback_data="admin_add")],
[types.InlineKeyboardButton(text="📋 Список администраторов", callback_data="admin_list")],
[types.InlineKeyboardButton(text="➖ Удалить администратора", callback_data="admin_remove")],
[types.InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")]
]
)

```
await callback.message.edit_text(
    "🛠 Управление администраторами",
    reply_markup=keyboard
)
```

@router.callback_query(F.data == "admin_add")
async def add_admin_start(callback: types.CallbackQuery, state: FSMContext):
await state.set_state(AddAdminState.user_id)

```
await callback.message.edit_text(
    "Введите user_id пользователя, которого нужно сделать администратором"
)
```

@router.message(AddAdminState.user_id)
async def add_admin_finish(message: types.Message, state: FSMContext, db: Database):
user_id = int(message.text)

```
await db.execute(
    """
    INSERT INTO admins (user_id)
    VALUES ($1)
    ON CONFLICT DO NOTHING
    """,
    user_id
)

await state.clear()

await message.answer("✅ Пользователь добавлен в администраторы")
```

@router.callback_query(F.data == "admin_list")
async def admin_list(callback: types.CallbackQuery, db: Database):
admins = await db.fetch("SELECT user_id FROM admins")

```
if not admins:
    text = "❌ Администраторов нет"
else:
    text = "🛠 Список администраторов\n\n"

    for admin in admins:
        text += f"ID: {admin['user_id']}\n"

await callback.message.edit_text(text)
```

@router.callback_query(F.data == "admin_remove")
async def admin_remove_menu(callback: types.CallbackQuery, db: Database):
admins = await db.fetch("SELECT user_id FROM admins")

```
keyboard = []

for admin in admins:
    if admin["user_id"] == SUPER_ADMIN_ID:
        continue

    keyboard.append(
        [types.InlineKeyboardButton(
            text=str(admin["user_id"]),
            callback_data=f"admin_delete_{admin['user_id']}"
        )]
    )

keyboard.append([types.InlineKeyboardButton(text="⬅ Назад", callback_data="admin_admins")])

await callback.message.edit_text(
    "Выберите администратора для удаления",
    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
)
```

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete(callback: types.CallbackQuery, db: Database):
user_id = int(callback.data.replace("admin_delete_", ""))

```
if user_id == SUPER_ADMIN_ID:
    await callback.answer("❌ Нельзя удалить супер администратора")
    return

await db.execute(
    "DELETE FROM admins WHERE user_id = $1",
    user_id
)

await callback.message.edit_text("❌ Администратор удалён")
```
