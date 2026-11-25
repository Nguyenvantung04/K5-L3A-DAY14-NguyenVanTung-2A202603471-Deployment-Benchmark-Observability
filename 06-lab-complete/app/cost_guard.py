"""
Cost guard (tiêu chí 8) — theo dõi chi phí LLM trong Redis.
"""
import datetime
import logging

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

logger = logging.getLogger(__name__)

# Giá USD / 1K tokens (tham khảo gpt-4o-mini)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def _cost_keys() -> tuple[str, str]:
    today = datetime.date.today()
    return f"cost:daily:{today.isoformat()}", f"cost:monthly:{today.strftime('%Y-%m')}"


def check_budget() -> None:
    """Gọi TRƯỚC khi gọi LLM. Hết budget → raise HTTPException(status_code=402)."""
    if r is None:
        logger.warning("Redis not configured; skipping budget check")
        return

    daily_key, monthly_key = _cost_keys()
    try:
        daily_spent = float(r.get(daily_key) or 0.0)
        monthly_spent = float(r.get(monthly_key) or 0.0)
    except Exception as exc:
        logger.warning("Redis budget read error (failing open): %s", exc)
        return

    if daily_spent >= settings.daily_budget_usd or monthly_spent >= settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail="LLM budget exceeded",
        )


def record_cost(input_tokens: int, output_tokens: int) -> float:
    """Gọi SAU khi gọi LLM. Cộng chi phí của request vào tổng, trả về chi phí request."""
    cost = (input_tokens / 1000.0) * PRICE_INPUT_PER_1K + (output_tokens / 1000.0) * PRICE_OUTPUT_PER_1K
    if r is None:
        return cost

    daily_key, monthly_key = _cost_keys()
    try:
        pipe = r.pipeline()
        pipe.incrbyfloat(daily_key, cost)
        pipe.expire(daily_key, 172800)  # 2 days
        pipe.incrbyfloat(monthly_key, cost)
        pipe.expire(monthly_key, 3024000)  # 35 days
        pipe.execute()
    except Exception as exc:
        logger.warning("Redis budget write error: %s", exc)
    return cost
