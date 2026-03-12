from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.row(KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина"))
    kb.row(KeyboardButton("📦 Мои заказы"), KeyboardButton("👤 Профиль"))
    kb.row(KeyboardButton("💰 Баланс"), KeyboardButton("👥 Рефералы"))
    kb.row(KeyboardButton("🆘 SOS"))
    return kb
