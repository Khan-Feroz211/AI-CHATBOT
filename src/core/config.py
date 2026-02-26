"""Application configuration classes."""

from __future__ import annotations

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/app.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    WHATSAPP_PROVIDER = os.environ.get("WHATSAPP_PROVIDER", "twilio")

    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID")
    META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
    META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
    META_APP_SECRET = os.environ.get("META_APP_SECRET")

    OTP_PROVIDER = os.environ.get("OTP_PROVIDER", "twilio")
    OTP_LENGTH = int(os.environ.get("OTP_LENGTH", 6))
    OTP_VALIDITY_MINUTES = int(os.environ.get("OTP_VALIDITY_MINUTES", 10))

    ADMIN_PHONE_NUMBERS = [
        n for n in os.environ.get("ADMIN_PHONE_NUMBERS", "").split(",") if n
    ]
    CLIENT_PHONE_NUMBERS = [
        n for n in os.environ.get("CLIENT_PHONE_NUMBERS", "").split(",") if n
    ]

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Inventory Business")
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")
    COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "")

    JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)
    JWT_EXPIRATION = timedelta(days=7)

    @staticmethod
    def init_app(_app):
        """Initialize app with config hooks."""


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Get configuration object based on FLASK_ENV."""
    environment = os.environ.get("FLASK_ENV", "development").lower()
    config_class = config.get(environment, config["default"])
    return config_class()
