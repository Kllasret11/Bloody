from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина"))
    kb.add(KeyboardButton("👤 Профиль"), KeyboardButton("📦 Мои заказы"))
    kb.add(KeyboardButton("🆘 SOS"))
    return kb


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Добавить категорию"), KeyboardButton("➕ Добавить товар"))
    kb.add(KeyboardButton("💲 Изменить цену"), KeyboardButton("💳 Пополнить баланс"))
    kb.add(KeyboardButton("📋 Все товары"), KeyboardButton("📑 Все заказы"))
    kb.add(KeyboardButton("🆘 Обращения"), KeyboardButton("✉️ Ответить на SOS"))
    kb.add(KeyboardButton("🚪 Выйти из админки"))
    return kb
