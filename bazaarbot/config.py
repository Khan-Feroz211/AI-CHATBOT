"""Environment-based configuration for BazaarBot."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask / server ────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    PORT: int = int(os.environ.get("PORT", 5000))

    # ── SQLite (legacy — keep alive for existing tests) ───────────────────
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "bazaarbot.db")

    # ── PostgreSQL (async, Day 2+) ────────────────────────────────────────
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bazaarbot",
    )
    DATABASE_POOL_SIZE: int = int(os.environ.get("DATABASE_POOL_SIZE", 10))

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")

    # ── JWT auth ──────────────────────────────────────────────────────────
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-this-in-production")
    JWT_EXPIRE_HOURS: int = int(os.environ.get("JWT_EXPIRE_HOURS", 24))
    API_KEY_HEADER: str = os.environ.get("API_KEY_HEADER", "X-API-Key")

    # ── Super-admin bootstrap credentials ────────────────────────────────
    SUPERADMIN_EMAIL: str = os.environ.get("SUPERADMIN_EMAIL", "")
    SUPERADMIN_PASSWORD: str = os.environ.get("SUPERADMIN_PASSWORD", "")

    # ── Twilio / WhatsApp ─────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM: str = os.environ.get(
        "TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"
    )
    WEBHOOK_VERIFY_TOKEN: str = os.environ.get("WEBHOOK_VERIFY_TOKEN", "")

    # ── Email (SMTP) ──────────────────────────────────────────────────────
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASS: str = os.environ.get("SMTP_PASS", "")
    NOTIFY_EMAIL: str = os.environ.get("NOTIFY_EMAIL", "")

    # ── Admin dashboard ───────────────────────────────────────────────────
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "bazaar123")

    # ── Rate limiting ─────────────────────────────────────────────────────
    RATE_LIMIT: str = os.environ.get("RATE_LIMIT", "30 per minute")

    # ── Multi-tenancy ─────────────────────────────────────────────────────
    DEFAULT_TENANT: str = os.environ.get("DEFAULT_TENANT", "default")


config = Config()
