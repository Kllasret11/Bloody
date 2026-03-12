from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def back_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.add(KeyboardButton("⬅ Назад"))
    return kb
