"""
Rate limiting (tiêu chí 7) — sliding window 60 giây lưu trong Redis (atomic Lua script).
"""
import logging
import secrets
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

logger = logging.getLogger(__name__)
WINDOW_SECONDS = 60

_SLIDING_WINDOW_LUA = """
redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, ARGV[1])
local count = redis.call("ZCARD", KEYS[1])
if count >= tonumber(ARGV[2]) then
    return 0
end
redis.call("ZADD", KEYS[1], ARGV[3], ARGV[4])
redis.call("EXPIRE", KEYS[1], tonumber(ARGV[5]))
return 1
"""


def check_rate_limit(key: str) -> None:
    """Giới hạn tối đa RATE_LIMIT_PER_MINUTE request / 60s cho mỗi API key."""
    if r is None:
        logger.warning("Redis not configured; skipping rate limit check")
        return

    now = time.time()
    window_start = now - WINDOW_SECONDS
    redis_key = f"ratelimit:{key}"
    member = f"{now}:{secrets.token_hex(4)}"

    try:
        allowed = r.eval(
            _SLIDING_WINDOW_LUA,
            1,
            redis_key,
            window_start,
            settings.rate_limit_per_minute,
            now,
            member,
            WINDOW_SECONDS + 5,
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Redis rate limit error (failing open): %s", exc)
