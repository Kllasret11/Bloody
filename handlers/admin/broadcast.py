from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from utils.database import Database

router = Router()

class BroadcastState(StatesGroup):
message = State()

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
await state.set_state(BroadcastState.message)
await callback.message.edit_text(
"📢 Введите сообщение для рассылки\n\n"
"Оно будет отправлено всем пользователям бота."
)

@router.message(BroadcastState.message)
async def broadcast_send(message: types.Message, state: FSMContext, db: Database):
text = message.text

```
users = await db.fetch("SELECT user_id FROM users")

success = 0
failed = 0

for user in users:
    try:
        await message.bot.send_message(user["user_id"], text)
        success += 1
        await asyncio.sleep(0.05)
    except:
        failed += 1

await state.clear()

await message.answer(
    f"📢 Рассылка завершена\n\n"
    f"✅ Отправлено: {success}\n"
    f"❌ Ошибок: {failed}"
)
