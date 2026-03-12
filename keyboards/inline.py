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
        InlineKeyboardButton("➖", callback_data=f"qty_minus:{product_id}:{qty}"),
        InlineKeyboardButton(f"{qty}", callback_data="qty_now"),
        InlineKeyboardButton("➕", callback_data=f"qty_plus:{product_id}:{qty}"),
    )
    kb.add(
        InlineKeyboardButton(
            "🛒 Добавить в корзину",
            callback_data=f"addcart:{product_id}:{qty}"
        )
    )
    return kb


def cart_item_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            "❌ Удалить",
            callback_data=f"cartdel:{product_id}"
        )
    )
    return kb


def checkout_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            "✅ Оформить заказ",
            callback_data="checkout"
        )
    )
    kb.add(
        InlineKeyboardButton(
            "🏷 Ввести промокод",
            callback_data="promo"
        )
    )
    return kb


def reorder_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            "🔁 Повторить заказ",
            callback_data=f"reorder:{int(order_id)}",
        )
    )
    return kb


def admin_order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("🚚 Доставляется", callback_data=f"ordstatus:{int(order_id)}:delivering"),
        InlineKeyboardButton("✅ Завершён", callback_data=f"ordstatus:{int(order_id)}:completed"),
    )
    return kb