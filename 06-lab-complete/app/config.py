"""
Config — 12-Factor: mọi cấu hình đọc từ biến môi trường.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    port: int = int(os.getenv("PORT") or "8000")
    environment: str = os.getenv("ENVIRONMENT") or "development"
    agent_api_key: str = os.getenv("AGENT_API_KEY") or ""
    redis_url: str = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE") or "10")
    daily_budget_usd: float = float(os.getenv("DAILY_BUDGET_USD") or "1.0")
    monthly_budget_usd: float = float(os.getenv("MONTHLY_BUDGET_USD") or "10.0")


settings = Settings()
