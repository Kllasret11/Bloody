from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина"))
    kb.add(KeyboardButton("💰 Баланс"), KeyboardButton("📦 Мои заказы"))
    return kb


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Добавить категорию"), KeyboardButton("➕ Добавить товар"))
    kb.add(KeyboardButton("💲 Изменить цену"), KeyboardButton("💳 Пополнить баланс"))
    kb.add(KeyboardButton("📋 Все товары"), KeyboardButton("📑 Все заказы"))
    kb.add(KeyboardButton("🚪 Выйти из админки"))
    return kb
