from __future__ import annotations

from typing import Any, Optional

import asyncpg


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        return self._pool

    async def execute(self, query: str, *args: Any) -> str:
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def setup(self) -> None:
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                balance NUMERIC(12,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_sessions (
                user_id BIGINT PRIMARY KEY,
                is_logged_in BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
                photo_file_id TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await self.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS photo_file_id TEXT")
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                user_id BIGINT NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
                PRIMARY KEY (user_id, product_id)
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                total_amount NUMERIC(12,2) NOT NULL,
                phone TEXT,
                address TEXT,
                status TEXT NOT NULL DEFAULT 'paid',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone TEXT")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS address TEXT")
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                product_name TEXT NOT NULL,
                price NUMERIC(12,2) NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0)
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                admin_reply TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                answered_at TIMESTAMPTZ
            )
            """
        )

    async def upsert_user(self, user_id: int, username: str | None, full_name: str) -> None:
        await self.execute(
            """
            INSERT INTO users (user_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET username = EXCLUDED.username, full_name = EXCLUDED.full_name
            """,
            user_id,
            username,
            full_name,
        )

    async def get_user(self, user_id: int):
        return await self.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

    async def set_admin_session(self, user_id: int, is_logged_in: bool) -> None:
        await self.execute(
            """
            INSERT INTO admin_sessions (user_id, is_logged_in)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET is_logged_in = EXCLUDED.is_logged_in, updated_at = NOW()
            """,
            user_id,
            is_logged_in,
        )

    async def is_admin_logged_in(self, user_id: int) -> bool:
        row = await self.fetchrow("SELECT is_logged_in FROM admin_sessions WHERE user_id = $1", user_id)
        return bool(row and row["is_logged_in"])

    async def add_category(self, name: str) -> None:
        await self.execute("INSERT INTO categories (name) VALUES ($1) ON CONFLICT (name) DO NOTHING", name)

    async def get_categories(self):
        return await self.fetch("SELECT id, name FROM categories ORDER BY id")

    async def get_category(self, category_id: int):
        return await self.fetchrow("SELECT id, name FROM categories WHERE id = $1", category_id)

    async def add_product(self, category_id: int, name: str, price: float, photo_file_id: str | None = None) -> None:
        await self.execute(
            "INSERT INTO products (category_id, name, price, photo_file_id) VALUES ($1, $2, $3, $4)",
            category_id,
            name,
            price,
            photo_file_id,
        )

    async def get_products_by_category(self, category_id: int):
        return await self.fetch(
            "SELECT id, name, price, photo_file_id FROM products WHERE category_id = $1 AND is_active = TRUE ORDER BY id",
            category_id,
        )

    async def get_all_products(self):
        return await self.fetch(
            """
            SELECT p.id, p.name, p.price, p.photo_file_id, c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE p.is_active = TRUE
            ORDER BY p.id
            """
        )

    async def get_product(self, product_id: int):
        return await self.fetchrow(
            "SELECT id, category_id, name, price, photo_file_id, is_active FROM products WHERE id = $1",
            product_id,
        )

    async def update_product_price(self, product_id: int, price: float) -> None:
        await self.execute("UPDATE products SET price = $2 WHERE id = $1", product_id, price)

    async def change_balance(self, user_id: int, amount: float) -> None:
        await self.execute(
            "UPDATE users SET balance = balance + $2 WHERE user_id = $1",
            user_id,
            amount,
        )

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        await self.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + 1
            """,
            user_id,
            product_id,
        )

    async def get_cart(self, user_id: int):
        return await self.fetch(
            """
            SELECT c.product_id, c.quantity, p.name, p.price
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = $1
            ORDER BY c.product_id
            """,
            user_id,
        )

    async def clear_cart(self, user_id: int) -> None:
        await self.execute("DELETE FROM cart_items WHERE user_id = $1", user_id)

    async def create_order_from_cart(self, user_id: int, address: str, phone: str) -> int:
        cart_items = await self.get_cart(user_id)
        if not cart_items:
            raise ValueError("Cart is empty")

        total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)
        user = await self.get_user(user_id)
        if user is None:
            raise ValueError("User not found")
        current_balance = float(user["balance"])
        if current_balance < total_amount:
            raise RuntimeError("INSUFFICIENT_FUNDS")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET balance = balance - $2 WHERE user_id = $1",
                    user_id,
                    total_amount,
                )
                order_id = await conn.fetchval(
                    "INSERT INTO orders (user_id, total_amount, address, phone) VALUES ($1, $2, $3, $4) RETURNING id",
                    user_id,
                    total_amount,
                    address,
                    phone,
                )
                for item in cart_items:
                    await conn.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        order_id,
                        item["product_id"],
                        item["name"],
                        item["price"],
                        item["quantity"],
                    )
                await conn.execute("DELETE FROM cart_items WHERE user_id = $1", user_id)
        return int(order_id)

    async def get_user_orders(self, user_id: int):
        return await self.fetch(
            "SELECT id, total_amount, address, phone, status, created_at FROM orders WHERE user_id = $1 ORDER BY id DESC",
            user_id,
        )

    async def get_all_orders(self):
        return await self.fetch(
            "SELECT id, user_id, total_amount, address, phone, status, created_at FROM orders ORDER BY id DESC LIMIT 50"
        )

    async def create_support_ticket(self, user_id: int, username: str | None, full_name: str, message: str) -> int:
        return int(
            await self.fetchval(
                """
                INSERT INTO support_tickets (user_id, username, full_name, message)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user_id,
                username,
                full_name,
                message,
            )
        )

    async def get_open_tickets(self):
        return await self.fetch(
            "SELECT id, user_id, username, full_name, message, created_at FROM support_tickets WHERE status = 'open' ORDER BY id DESC"
        )

    async def get_ticket(self, ticket_id: int):
        return await self.fetchrow("SELECT * FROM support_tickets WHERE id = $1", ticket_id)

    async def answer_ticket(self, ticket_id: int, reply_text: str) -> None:
        await self.execute(
            "UPDATE support_tickets SET status = 'answered', admin_reply = $2, answered_at = NOW() WHERE id = $1",
            ticket_id,
            reply_text,
        )
