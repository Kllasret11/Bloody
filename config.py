import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str
    admins: List[int]
    admin_login: str
    admin_password: str
    shop_title: str
    super_admin_id: int


def _parse_admins(raw: str) -> List[int]:
    values = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    return values


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    admins = _parse_admins(os.getenv("ADMINS", ""))

    # главный администратор
    super_admin_id = int(os.getenv("SUPER_ADMIN_ID", "1160081337"))

    # гарантируем что супер админ есть в списке админов
    if super_admin_id not in admins:
        admins.append(super_admin_id)

    return Config(
        bot_token=bot_token,
        database_url=database_url,
        admins=admins,
        admin_login=os.getenv("ADMIN_LOGIN", "Kllasret"),
        admin_password=os.getenv("ADMIN_PASSWORD", "123"),
        shop_title=os.getenv("SHOP_TITLE", "Магазин"),
        super_admin_id=super_admin_id,
    )