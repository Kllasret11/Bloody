from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup

from utils.database import Database

router = Router()

class PromoCreate(StatesGroup):
code = State()
percent = State()

def back_keyboard():
return InlineKeyboardMarkup(
inline_keyboard=[
[InlineKeyboardButton(text="⬅ Назад", callback_data="admin_promos")]
]
)

@router.callback_query(F.data == "promo_create")
async def promo_create_start(callback: types.CallbackQuery, state: FSMContext):
await state.set_state(PromoCreate.code)
await callback.message.edit_text(
"Введите название промокода\n\nПример: SALE10",
reply_markup=back_keyboard()
)

@router.message(StateFilter(PromoCreate.code))
async def promo_create_code(message: types.Message, state: FSMContext):
await state.update_data(code=message.text.upper())
await state.set_state(PromoCreate.percent)

```
await message.answer(
    "Введите процент скидки\n\nПример: 10"
)
```

@router.message(StateFilter(PromoCreate.percent))
async def promo_create_percent(message: types.Message, state: FSMContext, db: Database):
data = await state.get_data()

```
code = data["code"]
percent = int(message.text)

await db.execute(
    """
    INSERT INTO promo_codes (code, percent)
    VALUES ($1, $2)
    ON CONFLICT (code) DO NOTHING
    """,
    code,
    percent
)

await state.clear()

await message.answer(
    f"✅ Промокод создан\n\nКод: {code}\nСкидка: {percent}%",
    reply_markup=back_keyboard()
)
```

@router.callback_query(F.data == "promo_list")
async def promo_list(callback: types.CallbackQuery, db: Database):
promos = await db.fetch(
"""
SELECT code, percent, used_count
FROM promo_codes
WHERE is_active = TRUE
ORDER BY created_at DESC
"""
)

```
if not promos:
    text = "❌ Промокодов нет"
else:
    text = "🎟 Активные промокоды\n\n"
    for promo in promos:
        text += f"{promo['code']} — {promo['percent']}% (использован: {promo['used_count']})\n"

await callback.message.edit_text(
    text,
    reply_markup=back_keyboard()
)
```

@router.callback_query(F.data == "promo_delete")
async def promo_delete_menu(callback: types.CallbackQuery, db: Database):
promos = await db.fetch(
"""
SELECT code FROM promo_codes
WHERE is_active = TRUE
ORDER BY created_at DESC
"""
)

```
if not promos:
    await callback.message.edit_text(
        "❌ Нет промокодов для удаления",
        reply_markup=back_keyboard()
    )
    return

keyboard = []

for promo in promos:
    keyboard.append(
        [InlineKeyboardButton(
            text=promo["code"],
            callback_data=f"promo_remove_{promo['code']}"
        )]
    )

keyboard.append(
    [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_promos")]
)

await callback.message.edit_text(
    "Выберите промокод для удаления",
    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
)
```

@router.callback_query(F.data.startswith("promo_remove_"))
async def promo_remove(callback: types.CallbackQuery, db: Database):
code = callback.data.replace("promo_remove_", "")

```
await db.execute(
    "UPDATE promo_codes SET is_active = FALSE WHERE code = $1",
    code
)

await callback.message.edit_text(
    f"❌ Промокод {code} отключен",
    reply_markup=back_keyboard()
)
```
