"""WhatsApp provider setup helpers for Twilio and Meta Cloud API."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def detect_provider() -> str:
    """Detect configured WhatsApp provider from environment variables."""
    explicit = os.environ.get("WHATSAPP_PROVIDER", "").strip().lower()
    if explicit in {"twilio", "meta"}:
        return explicit

    has_twilio = bool(
        os.environ.get("TWILIO_ACCOUNT_SID") and os.environ.get("TWILIO_AUTH_TOKEN")
    )
    has_meta = bool(
        os.environ.get("META_ACCESS_TOKEN") and os.environ.get("META_PHONE_NUMBER_ID")
    )

    if has_twilio and not has_meta:
        return "twilio"
    if has_meta and not has_twilio:
        return "meta"
    return "unknown"


def setup_twilio() -> Dict[str, Any]:
    """Return Twilio setup status and required variables."""
    required = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_NUMBER"]
    missing = [name for name in required if not os.environ.get(name)]
    return {
        "provider": "twilio",
        "ready": not missing,
        "missing": missing,
        "webhook": "https://YOUR-DEPLOYED-URL/webhook",
    }


def setup_meta() -> Dict[str, Any]:
    """Return Meta Cloud API setup status and required variables."""
    required = [
        "META_ACCESS_TOKEN",
        "META_PHONE_NUMBER_ID",
        "META_WEBHOOK_VERIFY_TOKEN",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    return {
        "provider": "meta",
        "ready": not missing,
        "missing": missing,
        "webhook": "https://YOUR-DEPLOYED-URL/webhook",
    }


def parse_inbound_webhook(
    payload: Dict[str, Any], provider: Optional[str] = None
) -> Dict[str, Any]:
    """Normalize inbound webhook payload for Twilio and Meta formats."""
    selected = provider or detect_provider()
    if selected == "twilio":
        return {
            "provider": "twilio",
            "from": payload.get("From", ""),
            "to": payload.get("To", ""),
            "message": payload.get("Body", ""),
            "message_id": payload.get("MessageSid", ""),
        }

    if selected == "meta":
        message = (
            payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
        )
        return {
            "provider": "meta",
            "from": message.get("from", ""),
            "to": payload.get("metadata", {}).get("display_phone_number", ""),
            "message": message.get("text", {}).get("body", ""),
            "message_id": message.get("id", ""),
        }

    return {
        "provider": "unknown",
        "from": "",
        "to": "",
        "message": "",
        "message_id": "",
    }


def print_setup_instructions() -> None:
    """Print provider-specific setup guidance based on available environment variables."""
    provider = detect_provider()
    print(f"Detected provider: {provider}")

    if provider == "twilio":
        result = setup_twilio()
    elif provider == "meta":
        result = setup_meta()
    else:
        twilio_result = setup_twilio()
        meta_result = setup_meta()
        print("Set one provider in .env and fill all required values:")
        print(f"Twilio missing: {', '.join(twilio_result['missing']) or 'none'}")
        print(f"Meta missing: {', '.join(meta_result['missing']) or 'none'}")
        print("Webhook URL to configure: https://YOUR-DEPLOYED-URL/webhook")
        return

    if result["ready"]:
        print(f"{result['provider']} is ready.")
    else:
        print(f"Missing for {result['provider']}: {', '.join(result['missing'])}")

    print(f"Webhook URL to configure: {result['webhook']}")


if __name__ == "__main__":
    print_setup_instructions()
