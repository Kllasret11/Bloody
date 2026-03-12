from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.row(KeyboardButton("📊 Статистика"), KeyboardButton("📦 Заказы"))
    kb.row(KeyboardButton("👥 Пользователи"), KeyboardButton("🔎 Найти пользователя"))
    kb.row(KeyboardButton("➕ Добавить товар"), KeyboardButton("➕ Добавить категорию"))
    kb.row(KeyboardButton("✏️ Редактировать товар"), KeyboardButton("✏️ Редактировать категорию"))
    kb.row(KeyboardButton("🗑 Удалить товар"), KeyboardButton("🗑 Удалить категорию"))
    kb.row(KeyboardButton("💲 Изменить цену"), KeyboardButton("💰 Изменить баланс"))
    kb.row(KeyboardButton("🆘 Обращения"), KeyboardButton("✉️ Ответить на SOS"))
    kb.row(KeyboardButton("🚪 Выйти из админки"))
    return kb
