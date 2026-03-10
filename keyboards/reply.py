from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина"))
    kb.add(KeyboardButton("📦 Мои заказы"), KeyboardButton("👤 Профиль"))
    kb.add(KeyboardButton("🆘 SOS"))
    return kb


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📊 Статистика"), KeyboardButton("📦 Заказы"))
    kb.add(KeyboardButton("➕ Добавить товар"), KeyboardButton("➕ Добавить категорию"))
    kb.add(KeyboardButton("💰 Изменить баланс"), KeyboardButton("🆘 Обращения"))
    kb.add(KeyboardButton("✉️ Ответить на SOS"))
    kb.add(KeyboardButton("🚪 Выйти из админки"))
    return kb


def contact_request_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return kb


def delivery_method_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Отправить геопозицию"))
    kb.add(KeyboardButton("✍️ Ввести адрес вручную"))
    return kb


def location_request_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Отправить геопозицию", request_location=True))
    kb.add(KeyboardButton("✍️ Ввести адрес вручную"))
    return kb


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()