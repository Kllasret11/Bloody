from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def categories_kb(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for category in categories:
        kb.add(InlineKeyboardButton(category["name"], callback_data=f"cat:{category['id']}"))
    return kb


def product_item_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"addcart:{product_id}"))
    return kb


def cart_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
    kb.add(InlineKeyboardButton("🗑 Очистить корзину", callback_data="clearcart"))
    return kb

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def quantity_kb(product_id: int, qty: int = 1):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"qty_minus:{product_id}:{qty}"),
            InlineKeyboardButton(text=str(qty), callback_data="qty_now"),
            InlineKeyboardButton(text="➕", callback_data=f"qty_plus:{product_id}:{qty}")
        ],
        [
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_cart:{product_id}:{qty}")
        ]
    ])