"""Environment-based configuration for BazaarBot."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))

    # Database
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "bazaarbot.db")

    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    WEBHOOK_VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "")

    # Email (SMTP)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")

    # Admin
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "bazaar123")

    # Rate limiting
    RATE_LIMIT = os.environ.get("RATE_LIMIT", "30 per minute")

    # Default tenant slug
    DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "default")


config = Config()
