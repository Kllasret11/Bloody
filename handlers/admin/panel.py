from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import SUPER_ADMIN_ID
from utils.database import Database

router = Router()

def admin_panel_keyboard():
return InlineKeyboardMarkup(
inline_keyboard=[
[
InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders"),
InlineKeyboardButton(text="🛍 Товары", callback_data="admin_products"),
],
[
InlineKeyboardButton(text="📂 Категории", callback_data="admin_categories"),
InlineKeyboardButton(text="🎟 Промокоды", callback_data="admin_promos"),
],
[
InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
InlineKeyboardButton(text="💰 Баланс", callback_data="admin_balance"),
],
[
InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
InlineKeyboardButton(text="🛠 Администраторы", callback_data="admin_admins"),
],
[
InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
],
]
)

@router.message(Command("admin"))
async def admin_panel(message: types.Message, db: Database):
user_id = message.from_user.id

```
if user_id != SUPER_ADMIN_ID:
    is_admin = await db.fetchrow(
        "SELECT user_id FROM admins WHERE user_id = $1",
        user_id
    )
    if not is_admin:
        await message.answer("❌ У вас нет доступа к админ панели")
        return

await message.answer(
    "⚙️ Админ панель",
    reply_markup=admin_panel_keyboard()
)
```

@router.callback_query(F.data == "admin_promos")
async def promo_menu(callback: types.CallbackQuery):
keyboard = InlineKeyboardMarkup(
inline_keyboard=[
[InlineKeyboardButton(text="➕ Создать промокод", callback_data="promo_create")],
[InlineKeyboardButton(text="📋 Список промокодов", callback_data="promo_list")],
[InlineKeyboardButton(text="❌ Удалить промокод", callback_data="promo_delete")],
[InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")]
]
)

```
await callback.message.edit_text(
    "🎟 Управление промокодами",
    reply_markup=keyboard
)
```

@router.callback_query(F.data == "admin_back")
async def back_admin(callback: types.CallbackQuery):
await callback.message.edit_text(
"⚙️ Админ панель",
reply_markup=admin_panel_keyboard()
)
