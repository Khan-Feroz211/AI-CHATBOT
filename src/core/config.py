"""Application configuration classes."""

from __future__ import annotations

import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_database_url(url: str | None) -> str:
    """Normalize database URL for SQLAlchemy compatibility."""
    if not url:
        return "sqlite:///data/app.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if value:
        return value
    # Local fallback only; Railway should provide SECRET_KEY in environment variables.
    return secrets.token_urlsafe(32)


class Config:
    """Base configuration."""

    FLASK_ENV = os.environ.get("FLASK_ENV", "production").lower()
    DEBUG = _as_bool(os.environ.get("FLASK_DEBUG"), default=False)
    TESTING = False

    SECRET_KEY = _secret_key()

    DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "10")),
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "1800")),
    }

    REDIS_URL = os.environ.get("REDIS_URL")
    REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", "2.0"))
    REDIS_READ_TIMEOUT = float(os.environ.get("REDIS_READ_TIMEOUT", "2.0"))

    WHATSAPP_PROVIDER = os.environ.get("WHATSAPP_PROVIDER", "twilio")
    WHATSAPP_ENABLED = _as_bool(os.environ.get("WHATSAPP_ENABLED"), default=True)
    WHATSAPP_SANDBOX_MODE = _as_bool(
        os.environ.get("WHATSAPP_SANDBOX_MODE"), default=True
    )

    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID")
    META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
    META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
    META_APP_SECRET = os.environ.get("META_APP_SECRET")

    OTP_PROVIDER = os.environ.get("OTP_PROVIDER", "twilio")
    OTP_LENGTH = int(os.environ.get("OTP_LENGTH", "6"))
    OTP_VALIDITY_MINUTES = int(os.environ.get("OTP_VALIDITY_MINUTES", "10"))

    ADMIN_PHONE_NUMBERS = [
        n.strip() for n in os.environ.get("ADMIN_PHONE_NUMBERS", "").split(",") if n
    ]
    CLIENT_PHONE_NUMBERS = [
        n.strip() for n in os.environ.get("CLIENT_PHONE_NUMBERS", "").split(",") if n
    ]

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "")

    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Inventory Business")
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")
    COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "")

    JWT_SECRET = os.environ.get("JWT_SECRET") or os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_SECRET_KEY = JWT_SECRET
    SESSION_ENCRYPTION_KEY = os.environ.get("SESSION_ENCRYPTION_KEY")
    TOTP_ENCRYPTION_KEY = os.environ.get("TOTP_ENCRYPTION_KEY")
    JWT_EXPIRATION = timedelta(days=7)

    @staticmethod
    def init_app(_app):
        """Initialize app with config hooks."""


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    FLASK_ENV = "production"


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = False
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": ProductionConfig,
}


def get_config() -> Config:
    """Get configuration object based on FLASK_ENV."""
    environment = os.environ.get("FLASK_ENV", "production").lower()
    config_class = config.get(environment, config["default"])
    return config_class()
