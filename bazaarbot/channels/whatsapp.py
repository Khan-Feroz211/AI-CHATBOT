"""WhatsApp channel — Twilio integration for BazaarBot.

Implements BaseChannel so the intent router can treat WhatsApp the same
as any other channel.  The module-level ``send_whatsapp`` function is
kept for backward compatibility with existing Celery tasks.
"""
from __future__ import annotations

import logging

from bazaarbot.channels.base import (
    BaseChannel,
    ChannelMessage,
    ChannelResponse,
    ChannelType,
    register_channel,
)
from bazaarbot.config import config

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):
    """Twilio-backed WhatsApp channel."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.WHATSAPP

    def parse_incoming(
        self,
        payload: dict,
        tenant_slug: str,
    ) -> ChannelMessage | None:
        """Parse Twilio WhatsApp webhook form data into a ChannelMessage.

        Twilio POST fields used:
          Body       — message text
          From       — sender, e.g. ``whatsapp:+923001234567``
          To         — receiving number
          MessageSid — unique message identifier
          NumMedia   — number of attached media files
          MediaUrl0  — URL of the first media file (when present)

        Returns None for delivery-status webhooks that carry no Body or
        From values (Twilio sends those for read receipts, etc.).
        """
        body = payload.get("Body", "").strip()
        from_raw = payload.get("From", "")
        if not body and not from_raw:
            return None
        from_number = from_raw.replace("whatsapp:", "")
        return ChannelMessage(
            channel=ChannelType.WHATSAPP,
            from_number=from_number,
            text=body,
            tenant_slug=tenant_slug,
            raw_payload=payload,
            message_id=payload.get("MessageSid"),
            media_url=payload.get("MediaUrl0"),
        )

    async def send_message(self, response: ChannelResponse) -> bool:
        """Send a WhatsApp message via the Twilio REST API.

        Returns True on success, False on any error (errors are logged,
        not raised).
        """
        try:
            from twilio.rest import Client

            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            to_num = (
                response.to_number
                if response.to_number.startswith("whatsapp:")
                else f"whatsapp:{response.to_number}"
            )
            msg = client.messages.create(
                body=response.text,
                from_=config.TWILIO_WHATSAPP_FROM,
                to=to_num,
            )
            logger.info("WhatsApp sent SID=%s", msg.sid)
            return True
        except Exception as exc:
            logger.error("WhatsApp send failed: %s", exc)
            return False

    def verify_webhook(
        self,
        request_headers: dict,
        request_body: bytes,
        secret: str,
    ) -> bool:
        """Verify the Twilio ``X-Twilio-Signature`` header.

        In development mode (``APP_ENV=development``) the check is
        skipped and True is always returned so local testing is easy.
        """
        app_env = getattr(config, "APP_ENV", "production")
        if app_env == "development":
            return True
        try:
            from urllib.parse import parse_qs, parse_qsl

            from twilio.request_validator import RequestValidator

            validator = RequestValidator(secret)
            signature = request_headers.get("X-Twilio-Signature", "")
            url = request_headers.get("X-Original-URL", "")
            params = dict(parse_qsl(request_body.decode("utf-8", errors="replace")))
            return validator.validate(url, params, signature)
        except Exception as exc:
            logger.warning("WhatsApp webhook verification failed: %s", exc)
            return False

    def format_menu(self, options: list[str], title: str = "") -> str:
        """Format a numbered plain-text list suitable for WhatsApp."""
        lines: list[str] = []
        if title:
            lines.append(f"*{title}*")
            lines.append("")
        for i, opt in enumerate(options, 1):
            lines.append(f"{i}. {opt}")
        return "\n".join(lines)


# ── Register at module load ───────────────────────────────────────────────

_whatsapp_channel = WhatsAppChannel()
register_channel(_whatsapp_channel)


# ── Backward-compatible helper used by Celery tasks ───────────────────────

def send_whatsapp(to: str, body: str) -> bool:
    """Send a WhatsApp message via Twilio.

    Legacy helper kept for backward compatibility with existing Celery
    tasks.  New code should use ``WhatsAppChannel.send_message()``
    via the channel registry instead.

    Returns True on success, False on failure.
    """
    sid = config.TWILIO_ACCOUNT_SID
    token = config.TWILIO_AUTH_TOKEN
    if not sid or not token:
        print(f"[WhatsApp] Not configured — would send to {to}: {body[:60]}")
        return False
    try:
        from twilio.rest import Client

        client = Client(sid, token)
        to_num = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        msg = client.messages.create(
            body=body,
            from_=config.TWILIO_WHATSAPP_FROM,
            to=to_num,
        )
        print(f"[WhatsApp] Sent SID={msg.sid}")
        return True
    except Exception as exc:
        print(f"[WhatsApp] Error: {exc}")
        return False
