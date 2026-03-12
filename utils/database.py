from __future__ import annotations

import json
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

    async def fetch(self, query: str, *args: Any):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def setup(self) -> None:
        await self._setup_base_schema()
        await self._migrate()

    async def _setup_base_schema(self) -> None:
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                balance NUMERIC(12,2) NOT NULL DEFAULT 0,
                referrer_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
                referral_code TEXT UNIQUE,
                referral_reward_granted BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
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
                description TEXT,
                price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
                photo_file_id TEXT,
                stock INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

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
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

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

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    async def _get_schema_version(self) -> int:
        version = await self.fetchval(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
        )
        return int(version or 0)

    async def _ensure_constraint(
        self,
        conn: asyncpg.Connection,
        constraint_name: str,
        constraint_sql: str,
    ) -> None:
        exists = await conn.fetchval(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = $1
            """,
            constraint_name,
        )
        if not exists:
            await conn.execute(constraint_sql)

    async def _migrate(self) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                current = int(
                    await conn.fetchval(
                        "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
                    ) or 0
                )

                if current < 1:
                    await conn.execute(
                        """
                        ALTER TABLE products
                        ADD COLUMN IF NOT EXISTS stock INTEGER NOT NULL DEFAULT 0
                        """
                    )

                    await self._ensure_constraint(
                        conn,
                        "products_stock_non_negative",
                        """
                        ALTER TABLE products
                        ADD CONSTRAINT products_stock_non_negative
                        CHECK (stock >= 0)
                        """,
                    )

                    await conn.execute(
                        """
                        ALTER TABLE orders
                        ADD COLUMN IF NOT EXISTS applied_promo_code TEXT
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE orders
                        ADD COLUMN IF NOT EXISTS promo_percent INTEGER
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE orders
                        ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE orders
                        ALTER COLUMN status SET DEFAULT 'new'
                        """
                    )

                    await conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS promo_codes (
                            code TEXT PRIMARY KEY,
                            percent INTEGER NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            max_uses INTEGER,
                            used_count INTEGER NOT NULL DEFAULT 0,
                            expires_at TIMESTAMPTZ,
                            min_order_amount NUMERIC(12,2),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )

                    await self._ensure_constraint(
                        conn,
                        "promo_codes_percent_range",
                        """
                        ALTER TABLE promo_codes
                        ADD CONSTRAINT promo_codes_percent_range
                        CHECK (percent BETWEEN 1 AND 100)
                        """,
                    )

                    await self._ensure_constraint(
                        conn,
                        "promo_codes_used_count_non_negative",
                        """
                        ALTER TABLE promo_codes
                        ADD CONSTRAINT promo_codes_used_count_non_negative
                        CHECK (used_count >= 0)
                        """,
                    )

                    await conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS order_status_history (
                            id SERIAL PRIMARY KEY,
                            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                            status TEXT NOT NULL,
                            changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            changed_by BIGINT
                        )
                        """
                    )

                    await conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS admin_audit_log (
                            id SERIAL PRIMARY KEY,
                            admin_id BIGINT NOT NULL,
                            action TEXT NOT NULL,
                            payload JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )

                    await conn.execute(
                        """
                        INSERT INTO schema_migrations (version)
                        VALUES (1)
                        ON CONFLICT DO NOTHING
                        """
                    )

                if current < 2:
                    await conn.execute(
                        """
                        ALTER TABLE products
                        ADD COLUMN IF NOT EXISTS description TEXT
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS referrer_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS referral_code TEXT
                        """
                    )
                    await conn.execute(
                        """
                        ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS referral_reward_granted BOOLEAN NOT NULL DEFAULT FALSE
                        """
                    )
                    await conn.execute(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code_unique
                        ON users(referral_code)
                        WHERE referral_code IS NOT NULL
                        """
                    )
                    await conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS referral_rewards (
                            id SERIAL PRIMARY KEY,
                            referrer_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                            referred_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                            order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
                            reward_amount NUMERIC(12,2) NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            UNIQUE(referred_user_id)
                        )
                        """
                    )
                    await conn.execute(
                        """
                        INSERT INTO schema_migrations (version)
                        VALUES (2)
                        ON CONFLICT DO NOTHING
                        """
                    )

    async def upsert_user(self, user_id: int, username: str | None, full_name: str, referrer_id: int | None = None) -> None:
        user_id = int(user_id)
        if referrer_id is not None:
            try:
                referrer_id = int(referrer_id)
            except (TypeError, ValueError):
                referrer_id = None

        await self.execute(
            """
            INSERT INTO users (user_id, username, full_name, referrer_id, referral_code)
            VALUES (
                $1::bigint,
                $2::text,
                $3::text,
                CASE WHEN $4::bigint = $1::bigint THEN NULL ELSE $4::bigint END,
                CONCAT('ref_', $1::bigint)
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                referrer_id = COALESCE(users.referrer_id, EXCLUDED.referrer_id),
                referral_code = COALESCE(users.referral_code, EXCLUDED.referral_code)
            """,
            user_id,
            username,
            full_name,
            referrer_id,
        )

    async def get_user(self, user_id: int):
        return await self.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id,
        )

    async def list_users(self, limit: int = 20, offset: int = 0):
        limit = max(1, min(100, int(limit)))
        offset = max(0, int(offset))
        return await self.fetch(
            """
            SELECT user_id, username, full_name, balance, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

    async def change_balance(self, user_id: int, amount: float) -> None:
        await self.execute(
            """
            UPDATE users
            SET balance = balance + $2
            WHERE user_id = $1
            """,
            user_id,
            amount,
        )

    async def set_admin_session(self, user_id: int, is_logged_in: bool) -> None:
        await self.execute(
            """
            INSERT INTO admin_sessions (user_id, is_logged_in)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET
                is_logged_in = EXCLUDED.is_logged_in,
                updated_at = NOW()
            """,
            user_id,
            is_logged_in,
        )

    async def is_admin_logged_in(self, user_id: int) -> bool:
        row = await self.fetchrow(
            "SELECT is_logged_in FROM admin_sessions WHERE user_id = $1",
            user_id,
        )
        return bool(row and row["is_logged_in"])

    async def log_admin_action(
        self,
        admin_id: int,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await self.execute(
            """
            INSERT INTO admin_audit_log (admin_id, action, payload)
            VALUES ($1, $2, $3)
            """,
            admin_id,
            action,
            json.dumps(payload) if payload is not None else None,
        )

    async def is_admin(self, user_id: int) -> bool:
        row = await self.fetchrow(
            "SELECT user_id FROM admins WHERE user_id = $1",
            user_id,
        )
        return row is not None

    async def add_admin(self, user_id: int) -> None:
        await self.execute(
            """
            INSERT INTO admins (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )

    async def remove_admin(self, user_id: int) -> None:
        await self.execute(
            "DELETE FROM admins WHERE user_id = $1",
            user_id,
        )

    async def list_admins(self):
        return await self.fetch(
            """
            SELECT user_id, created_at
            FROM admins
            ORDER BY created_at ASC
            """
        )

    async def add_category(self, name: str):
        return await self.fetchval(
            """
            INSERT INTO categories (name)
            VALUES ($1)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
            """,
            name,
        )

    async def get_categories(self):
        return await self.fetch(
            "SELECT id, name FROM categories ORDER BY id"
        )

    async def get_category(self, category_id: int):
        return await self.fetchrow(
            "SELECT id, name FROM categories WHERE id = $1",
            category_id,
        )

    async def update_category_name(self, category_id: int, new_name: str) -> None:
        await self.execute(
            """
            UPDATE categories
            SET name = $2
            WHERE id = $1
            """,
            category_id,
            new_name,
        )

    async def category_has_products(self, category_id: int) -> bool:
        count = await self.fetchval(
            "SELECT COUNT(*) FROM products WHERE category_id = $1",
            category_id,
        )
        return int(count or 0) > 0

    async def delete_category(self, category_id: int) -> None:
        await self.execute(
            "DELETE FROM categories WHERE id = $1",
            category_id,
        )

    async def add_product(
        self,
        category_id: int,
        name: str,
        price: float,
        photo_file_id: str | None = None,
        stock: int = 0,
        description: str | None = None,
    ) -> int:
        stock = max(0, int(stock))
        product_id = await self.fetchval(
            """
            INSERT INTO products (
                category_id,
                name,
                description,
                price,
                photo_file_id,
                stock
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            category_id,
            name,
            description,
            price,
            photo_file_id,
            stock,
        )
        return int(product_id)

    async def get_products_by_category(self, category_id: int):
        return await self.fetch(
            """
            SELECT id, name, description, price, photo_file_id, stock
            FROM products
            WHERE category_id = $1 AND is_active = TRUE
            ORDER BY id
            """,
            category_id,
        )

    async def get_products_by_category_available(self, category_id: int):
        return await self.fetch(
            """
            SELECT id, name, description, price, photo_file_id, stock
            FROM products
            WHERE category_id = $1 AND is_active = TRUE AND stock > 0
            ORDER BY id
            """,
            category_id,
        )

    async def get_all_products(self):
        return await self.fetch(
            """
            SELECT
                p.id,
                p.name,
                p.price,
                p.photo_file_id,
                p.stock,
                p.category_id,
                c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE p.is_active = TRUE
            ORDER BY p.id
            """
        )

    async def get_product(self, product_id: int):
        return await self.fetchrow(
            """
            SELECT id, category_id, name, description, price, photo_file_id, is_active, stock
            FROM products
            WHERE id = $1
            """,
            product_id,
        )

    async def get_product_available(self, product_id: int):
        return await self.fetchrow(
            """
            SELECT id, category_id, name, description, price, photo_file_id, is_active, stock
            FROM products
            WHERE id = $1 AND is_active = TRUE AND stock > 0
            """,
            product_id,
        )

    async def set_product_stock(self, product_id: int, stock: int) -> None:
        stock = max(0, int(stock))
        await self.execute(
            """
            UPDATE products
            SET stock = $2
            WHERE id = $1
            """,
            product_id,
            stock,
        )

    async def decrease_stock_if_available(
        self,
        product_id: int,
        quantity: int,
        conn: asyncpg.Connection,
    ) -> bool:
        quantity = max(1, int(quantity))
        res = await conn.execute(
            """
            UPDATE products
            SET stock = stock - $2
            WHERE id = $1 AND is_active = TRUE AND stock >= $2
            """,
            product_id,
            quantity,
        )
        return str(res).endswith("1")

    async def update_product_name(self, product_id: int, new_name: str) -> None:
        await self.execute(
            """
            UPDATE products
            SET name = $2
            WHERE id = $1
            """,
            product_id,
            new_name,
        )

    async def update_product_price(self, product_id: int, price: float) -> None:
        await self.execute(
            """
            UPDATE products
            SET price = $2
            WHERE id = $1
            """,
            product_id,
            price,
        )

    async def update_product_photo(self, product_id: int, photo_file_id: str | None) -> None:
        await self.execute(
            """
            UPDATE products
            SET photo_file_id = $2
            WHERE id = $1
            """,
            product_id,
            photo_file_id,
        )

    async def update_product_category(self, product_id: int, category_id: int) -> None:
        await self.execute(
            """
            UPDATE products
            SET category_id = $2
            WHERE id = $1
            """,
            product_id,
            category_id,
        )

    async def update_product_description(self, product_id: int, description: str | None) -> None:
        await self.execute(
            """
            UPDATE products
            SET description = $2
            WHERE id = $1
            """,
            product_id,
            description,
        )

    async def set_product_active(self, product_id: int, is_active: bool) -> None:
        await self.execute(
            """
            UPDATE products
            SET is_active = $2
            WHERE id = $1
            """,
            product_id,
            is_active,
        )

    async def delete_product(self, product_id: int) -> None:
        await self.execute(
            "DELETE FROM products WHERE id = $1",
            product_id,
        )

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        quantity = max(1, int(quantity))
        await self.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
            """,
            user_id,
            product_id,
            quantity,
        )

    async def get_cart(self, user_id: int):
        return await self.fetch(
            """
            SELECT
                c.product_id,
                c.quantity,
                p.name,
                p.price,
                p.stock,
                p.is_active
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = $1
            ORDER BY c.product_id
            """,
            user_id,
        )

    async def remove_cart_item(self, product_id: int, user_id: int) -> None:
        await self.execute(
            """
            DELETE FROM cart_items
            WHERE product_id = $1 AND user_id = $2
            """,
            product_id,
            user_id,
        )

    async def clear_cart(self, user_id: int) -> None:
        await self.execute(
            "DELETE FROM cart_items WHERE user_id = $1",
            user_id,
        )

    async def get_promo(self, code: str):
        code = (code or "").strip().upper()
        if not code:
            return None

        return await self.fetchrow(
            """
            SELECT *
            FROM promo_codes
            WHERE code = $1
              AND is_active = TRUE
              AND (expires_at IS NULL OR expires_at > NOW())
              AND (max_uses IS NULL OR used_count < max_uses)
            """,
            code,
        )

    async def create_promo(
        self,
        code: str,
        percent: int,
        max_uses: int | None = None,
        expires_at=None,
        min_order_amount: float | None = None,
    ) -> None:
        code = (code or "").strip().upper()
        await self.execute(
            """
            INSERT INTO promo_codes (
                code,
                percent,
                max_uses,
                expires_at,
                min_order_amount
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (code) DO UPDATE SET
                percent = EXCLUDED.percent,
                max_uses = EXCLUDED.max_uses,
                expires_at = EXCLUDED.expires_at,
                min_order_amount = EXCLUDED.min_order_amount,
                is_active = TRUE
            """,
            code,
            percent,
            max_uses,
            expires_at,
            min_order_amount,
        )

    async def get_all_promos(self):
        return await self.fetch(
            """
            SELECT
                code,
                percent,
                is_active,
                max_uses,
                used_count,
                expires_at,
                min_order_amount,
                created_at
            FROM promo_codes
            ORDER BY created_at DESC
            """
        )

    async def deactivate_promo(self, code: str) -> None:
        code = (code or "").strip().upper()
        await self.execute(
            """
            UPDATE promo_codes
            SET is_active = FALSE
            WHERE code = $1
            """,
            code,
        )

    async def increment_promo_use(self, code: str, conn: asyncpg.Connection) -> None:
        code = (code or "").strip().upper()
        await conn.execute(
            """
            UPDATE promo_codes
            SET used_count = used_count + 1
            WHERE code = $1
            """,
            code,
        )

    async def create_order_from_cart(
        self,
        user_id: int,
        phone: str,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        promo_code: str | None = None,
    ) -> int:
        cart_items = await self.get_cart(user_id)
        if not cart_items:
            raise ValueError("Cart is empty")

        for item in cart_items:
            if not item["is_active"] or int(item["stock"]) <= 0:
                raise RuntimeError("OUT_OF_STOCK")

        total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)

        user = await self.get_user(user_id)
        if user is None:
            raise ValueError("User not found")

        if float(user["balance"]) < total_amount:
            raise RuntimeError("INSUFFICIENT_FUNDS")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                cart_items = await conn.fetch(
                    """
                    SELECT
                        c.product_id,
                        c.quantity,
                        p.name,
                        p.price,
                        p.stock,
                        p.is_active
                    FROM cart_items c
                    JOIN products p ON p.id = c.product_id
                    WHERE c.user_id = $1
                    ORDER BY c.product_id
                    """,
                    user_id,
                )

                if not cart_items:
                    raise ValueError("Cart is empty")

                for item in cart_items:
                    if not item["is_active"] or int(item["stock"]) <= 0:
                        raise RuntimeError("OUT_OF_STOCK")

                total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)

                promo_percent: int | None = None
                discount_amount = 0.0
                applied_promo_code: str | None = None

                if promo_code:
                    promo = await self.get_promo(promo_code)
                    if promo:
                        min_order_amount = promo["min_order_amount"]
                        if min_order_amount is None or total_amount >= float(min_order_amount):
                            promo_percent = int(promo["percent"])
                            applied_promo_code = str(promo["code"])
                            discount_amount = round(total_amount * (promo_percent / 100.0), 2)
                            total_amount = max(0.0, round(total_amount - discount_amount, 2))

                balance_res = await conn.execute(
                    """
                    UPDATE users
                    SET balance = balance - $2
                    WHERE user_id = $1 AND balance >= $2
                    """,
                    user_id,
                    total_amount,
                )
                if not str(balance_res).endswith("1"):
                    raise RuntimeError("INSUFFICIENT_FUNDS")

                for item in cart_items:
                    ok = await self.decrease_stock_if_available(
                        int(item["product_id"]),
                        int(item["quantity"]),
                        conn,
                    )
                    if not ok:
                        raise RuntimeError("OUT_OF_STOCK")

                order_id = await conn.fetchval(
                    """
                    INSERT INTO orders (
                        user_id,
                        total_amount,
                        phone,
                        address,
                        latitude,
                        longitude,
                        status,
                        applied_promo_code,
                        promo_percent,
                        discount_amount
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    user_id,
                    total_amount,
                    phone,
                    address,
                    latitude,
                    longitude,
                    "new",
                    applied_promo_code,
                    promo_percent,
                    discount_amount,
                )

                for item in cart_items:
                    await conn.execute(
                        """
                        INSERT INTO order_items (
                            order_id,
                            product_id,
                            product_name,
                            price,
                            quantity
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        order_id,
                        item["product_id"],
                        item["name"],
                        item["price"],
                        item["quantity"],
                    )

                if applied_promo_code:
                    await self.increment_promo_use(applied_promo_code, conn)

                await conn.execute(
                    "DELETE FROM cart_items WHERE user_id = $1",
                    user_id,
                )

                await conn.execute(
                    """
                    INSERT INTO order_status_history (order_id, status, changed_by)
                    VALUES ($1, $2, $3)
                    """,
                    order_id,
                    "new",
                    None,
                )

        await self._grant_referral_reward_if_needed(user_id=int(user_id), order_id=int(order_id))
        return int(order_id)

    async def get_order(self, order_id: int):
        return await self.fetchrow(
            "SELECT * FROM orders WHERE id = $1",
            order_id,
        )

    async def update_order_status(self, order_id: int, status: str) -> None:
        await self.execute(
            """
            UPDATE orders
            SET status = $1
            WHERE id = $2
            """,
            status,
            order_id,
        )

    async def set_order_status(
        self,
        order_id: int,
        status: str,
        changed_by: int | None = None,
    ) -> None:
        await self.execute(
            """
            UPDATE orders
            SET status = $2
            WHERE id = $1
            """,
            order_id,
            status,
        )
        await self.execute(
            """
            INSERT INTO order_status_history (order_id, status, changed_by)
            VALUES ($1, $2, $3)
            """,
            order_id,
            status,
            changed_by,
        )

    async def get_order_items(self, order_id: int):
        return await self.fetch(
            """
            SELECT product_id, product_name, price, quantity
            FROM order_items
            WHERE order_id = $1
            ORDER BY id
            """,
            order_id,
        )

    async def get_user_orders(self, user_id: int):
        return await self.fetch(
            """
            SELECT
                id,
                total_amount,
                address,
                phone,
                latitude,
                longitude,
                status,
                created_at
            FROM orders
            WHERE user_id = $1
            ORDER BY id DESC
            """,
            user_id,
        )

    async def get_all_orders(self):
        return await self.fetch(
            """
            SELECT
                id,
                user_id,
                total_amount,
                address,
                phone,
                latitude,
                longitude,
                status,
                created_at
            FROM orders
            ORDER BY id DESC
            LIMIT 100
            """
        )

    async def get_active_orders(self):
        return await self.fetch(
            """
            SELECT
                id,
                user_id,
                total_amount,
                address,
                phone,
                latitude,
                longitude,
                status,
                created_at
            FROM orders
            WHERE status NOT IN ('completed', 'done', 'cancelled')
            ORDER BY id DESC
            LIMIT 100
            """
        )

    async def get_archive_orders(self):
        return await self.fetch(
            """
            SELECT
                id,
                user_id,
                total_amount,
                address,
                phone,
                latitude,
                longitude,
                status,
                created_at
            FROM orders
            WHERE status IN ('completed', 'done', 'cancelled')
            ORDER BY id DESC
            LIMIT 100
            """
        )

    async def create_support_ticket(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        message: str,
    ) -> int:
        ticket_id = await self.fetchval(
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
        return int(ticket_id)

    async def get_open_tickets(self):
        return await self.fetch(
            """
            SELECT
                id,
                user_id,
                username,
                full_name,
                message,
                created_at
            FROM support_tickets
            WHERE status = 'open'
            ORDER BY id DESC
            """
        )

    async def get_ticket(self, ticket_id: int):
        return await self.fetchrow(
            "SELECT * FROM support_tickets WHERE id = $1",
            ticket_id,
        )

    async def answer_ticket(self, ticket_id: int, reply_text: str) -> None:
        await self.execute(
            """
            UPDATE support_tickets
            SET status = 'answered',
                admin_reply = $2,
                answered_at = NOW()
            WHERE id = $1
            """,
            ticket_id,
            reply_text,
        )

    async def _grant_referral_reward_if_needed(self, user_id: int, order_id: int) -> None:
        user = await self.get_user(user_id)
        if not user or user["referrer_id"] is None or bool(user["referral_reward_granted"]):
            return

        previous_orders = await self.fetchval(
            "SELECT COUNT(*) FROM orders WHERE user_id = $1 AND id <> $2",
            user_id,
            order_id,
        )
        if int(previous_orders or 0) > 0:
            return

        from config import load_config
        cfg = load_config()
        reward_referrer = float(cfg.referral_reward_referrer)
        reward_new = float(cfg.referral_reward_new_user)
        referrer_id = int(user['referrer_id'])

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                exists = await conn.fetchval(
                    "SELECT 1 FROM referral_rewards WHERE referred_user_id = $1",
                    user_id,
                )
                if exists:
                    return
                await conn.execute(
                    "UPDATE users SET balance = balance + $2 WHERE user_id = $1",
                    referrer_id, reward_referrer,
                )
                await conn.execute(
                    "UPDATE users SET balance = balance + $2, referral_reward_granted = TRUE WHERE user_id = $1",
                    user_id, reward_new,
                )
                await conn.execute(
                    """
                    INSERT INTO referral_rewards (referrer_id, referred_user_id, order_id, reward_amount)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (referred_user_id) DO NOTHING
                    """,
                    referrer_id, user_id, order_id, reward_referrer,
                )

    async def get_referral_stats(self, user_id: int) -> dict[str, float | int]:
        referrals_count = await self.fetchval(
            "SELECT COUNT(*) FROM users WHERE referrer_id = $1", user_id
        )
        successful_referrals = await self.fetchval(
            "SELECT COUNT(*) FROM referral_rewards WHERE referrer_id = $1", user_id
        )
        earned_bonus = await self.fetchval(
            "SELECT COALESCE(SUM(reward_amount), 0) FROM referral_rewards WHERE referrer_id = $1", user_id
        )
        return {
            "referrals_count": int(referrals_count or 0),
            "successful_referrals": int(successful_referrals or 0),
            "earned_bonus": float(earned_bonus or 0),
        }

    async def get_order_status_history(self, order_id: int):
        return await self.fetch(
            """
            SELECT order_id, status, changed_at, changed_by
            FROM order_status_history
            WHERE order_id = $1
            ORDER BY id DESC
            """,
            order_id,
        )
