from __future__ import annotations

import time

_last: dict[tuple[int, str], float] = {}


def hit(user_id: int, key: str, seconds: float) -> bool:
    """
    Returns True if action is allowed, False if rate-limited.
    """
    now = time.time()
    k = (int(user_id), str(key))
    prev = _last.get(k, 0.0)
    if now - prev < seconds:
        return False
    _last[k] = now
    return True

