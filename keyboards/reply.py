from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False
    )

    kb.row(
        KeyboardButton("🛍 Каталог"),
        KeyboardButton("🛒 Корзина")
    )

    kb.row(
        KeyboardButton("📦 Мои заказы"),
        KeyboardButton("👤 Профиль")
    )

    kb.row(
        KeyboardButton("🆘 SOS")
    )

    return kb


def admin_menu() -> ReplyKeyboardMarkup:

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


    kb.row(
        KeyboardButton("📊 Статистика"),
        KeyboardButton("📦 Заказы")
    )

    kb.row(
        KeyboardButton("➕ Добавить товар"),
        KeyboardButton("➕ Добавить категорию")
    )

    kb.row(
        KeyboardButton("✏️ Редактировать товар"),
        KeyboardButton("✏️ Редактировать категорию")
    )

    kb.row(
        KeyboardButton("🗑 Удалить товар"),
        KeyboardButton("🗑 Удалить категорию")
    )

    kb.row(
        KeyboardButton("💰 Изменить баланс")
    )

    kb.row(
        KeyboardButton("🆘 Обращения"),
        KeyboardButton("✉️ Ответить на SOS")
    )

    kb.row(
        KeyboardButton("🚪 Выйти из админки")
    )

    return kb


def contact_request_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    kb.add(
        KeyboardButton(
            "📱 Отправить номер телефона",
            request_contact=True
        )
    )

    return kb


def delivery_method_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    kb.add(
        KeyboardButton("📍 Отправить геопозицию")
    )

    kb.add(
        KeyboardButton("✍️ Ввести адрес вручную")
    )

    return kb


def location_request_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    kb.add(
        KeyboardButton(
            "📍 Отправить геопозицию",
            request_location=True
        )
    )

    kb.add(
        KeyboardButton("✍️ Ввести адрес вручную")
    )

    return kb


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()