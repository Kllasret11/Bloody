from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def categories_kb(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for category in categories:
        kb.add(InlineKeyboardButton(category["name"], callback_data=f"cat:{category['id']}"))
    return kb


def products_kb(products) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for product in products:
        kb.add(
            InlineKeyboardButton(
                f"{product['name']} — {float(product['price']):.2f}",
                callback_data=f"addcart:{product['id']}",
            )
        )
    return kb


def cart_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
    kb.add(InlineKeyboardButton("🗑 Очистить корзину", callback_data="clearcart"))
    return kb
