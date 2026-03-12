from loader import config


def build_referral_code(user_id: int) -> str:
    return f"ref_{int(user_id)}"


def parse_referral_payload(payload: str | None) -> int | None:
    if not payload:
        return None
    payload = payload.strip()
    if payload.startswith("ref_"):
        payload = payload[4:]
    if not payload.isdigit():
        return None
    return int(payload)


def referral_summary_text(user, stats: dict, bot_username: str) -> str:
    link = f"https://t.me/{bot_username}?start={build_referral_code(int(user['user_id']))}"
    return (
        "<b>👥 Реферальная программа</b>\n\n"
        f"Твоя ссылка:\n<code>{link}</code>\n\n"
        f"Приглашено пользователей: <b>{stats['referrals_count']}</b>\n"
        f"Успешных приглашений: <b>{stats['successful_referrals']}</b>\n"
        f"Заработано бонусов: <b>{stats['earned_bonus']:.2f}</b>\n\n"
        f"За каждого приглашённого после первого заказа: <b>+{config.referral_reward_referrer}</b>\n"
        f"Новому пользователю приветственный бонус: <b>+{config.referral_reward_new_user}</b>"
    )
