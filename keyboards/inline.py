from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MIN_QTY = 1
MAX_QTY = 99


def categories_kb(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for category in categories:
        kb.add(
            InlineKeyboardButton(
                text=category.get("name", "Категория"),
                callback_data=f"cat:{category.get('id')}"
            )
        )
    return kb


def product_item_kb(product_id: int, qty: int = 1) -> InlineKeyboardMarkup:
    qty = max(MIN_QTY, min(MAX_QTY, int(qty)))

    kb = InlineKeyboardMarkup(row_width=3)
    kb.row(
        InlineKeyboardButton("➖", callback_data=f"qty:{product_id}:{qty}:minus"),
        InlineKeyboardButton(f"{qty}", callback_data="qty:noop"),
        InlineKeyboardButton("➕", callback_data=f"qty:{product_id}:{qty}:plus"),
    )
    kb.add(
        InlineKeyboardButton(
            "🛒 Добавить в корзину",
            callback_data=f"addcart:{product_id}:{qty}"
        )
    )
    return kb


def cart_item_kb(item_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("❌ Удалить", callback_data=f"cartdel:{item_id}"))
    return kb


def checkout_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
    return kb