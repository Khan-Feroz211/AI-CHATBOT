"""Telegram bot channel for BazaarBot.

Implements BaseChannel using the Telegram Bot API over HTTPS.
Webhook verification uses the ``X-Telegram-Bot-Api-Secret-Token``
header that Telegram sends when the webhook is registered with a
``secret_token`` parameter.

Setup:
  1. Create a bot via @BotFather and copy the token.
  2. Set TELEGRAM_BOT_TOKEN (and optionally TELEGRAM_WEBHOOK_SECRET)
     in your environment.
  3. Register the webhook once after deploy:
       await TelegramChannel().setup_webhook(
           "https://your-domain.com/webhook/telegram/{slug}",
           secret_token=config.TELEGRAM_WEBHOOK_SECRET,
       )
  4. Telegram will POST to that URL for every message.
"""
from __future__ import annotations

import hmac
import logging

import httpx

from bazaarbot.channels.base import (
    BaseChannel,
    ChannelMessage,
    ChannelResponse,
    ChannelType,
    register_channel,
)
from bazaarbot.config import config

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"

# Telegram commands mapped to normalised intent strings understood by the
# intent router.  Any command not in this map is forwarded as-is (with the
# slash stripped) so the router can attempt NLP classification.
_COMMAND_MAP: dict[str, str] = {
    "/start": "hello",
    "/help": "help",
    "/stock": "stock",
    "/menu": "menu",
}


class TelegramChannel(BaseChannel):
    """Telegram Bot API channel."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.TELEGRAM

    # ── Inbound ──────────────────────────────────────────────────────────

    def parse_incoming(
        self,
        payload: dict,
        tenant_slug: str,
    ) -> ChannelMessage | None:
        """Parse a Telegram webhook JSON payload into a ChannelMessage.

        Handles regular text messages and bot commands (``/start``,
        ``/help``, ``/stock``, ``/order``, etc.).

        Returns None for:
          - Edited messages (``edited_message`` key)
          - Channel posts (``channel_post`` key)
          - Inline queries and any other non-``message`` update types
          - Messages without a text body (stickers, voice notes, etc.)

        ``from_number`` is encoded as ``TGID:{chat_id}`` so it is
        unique across channels and does not conflict with phone numbers
        used by WhatsApp/SMS.
        """
        # Ignore non-message updates
        if "edited_message" in payload or "channel_post" in payload:
            return None

        message = payload.get("message")
        if not message:
            return None

        text = message.get("text", "").strip()
        if not text:
            return None

        chat = message.get("chat")
        if not chat or "id" not in chat:
            return None
        chat_id = str(chat["id"])

        # Normalise bot commands to intent-router-friendly strings
        if text.startswith("/"):
            command = text.split()[0].lower()
            # Strip @botname suffix that Telegram appends in group chats
            command = command.split("@")[0]
            if command in _COMMAND_MAP:
                text = _COMMAND_MAP[command]
            elif command == "/order":
                # "/order rice 5" → "order rice 5"; bare "/order" → "order"
                remainder = text.removeprefix("/order").strip()
                text = f"order {remainder}".strip()
            else:
                # Unknown command — strip slash and forward to NLP
                text = text.lstrip("/").strip()
                if not text:
                    return None

        return ChannelMessage(
            channel=ChannelType.TELEGRAM,
            from_number=f"TGID:{chat_id}",
            text=text,
            tenant_slug=tenant_slug,
            raw_payload=payload,
            message_id=str(message.get("message_id", "")),
        )

    # ── Outbound ─────────────────────────────────────────────────────────

    async def send_message(self, response: ChannelResponse) -> bool:
        """Send a message via the Telegram Bot API ``sendMessage`` method.

        Supports plain text, Markdown formatting, and optional inline
        keyboard buttons via ``response.reply_markup``.

        ``response.to_number`` must be in the ``TGID:{chat_id}`` format
        produced by ``parse_incoming``.

        Returns True on success, False on failure (errors are logged,
        never raised).
        """
        if not config.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not configured — cannot send message")
            return False

        chat_id = response.to_number.replace("TGID:", "")
        url = f"{TELEGRAM_API}/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"

        parse_mode = response.parse_mode or "Markdown"
        payload: dict = {
            "chat_id": chat_id,
            "text": response.text,
            "parse_mode": parse_mode,
        }
        if response.reply_markup:
            payload["reply_markup"] = response.reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(
                    "Telegram sendMessage failed [%s]: %s",
                    resp.status_code,
                    resp.text,
                )
                return False
            return True
        except Exception as exc:
            logger.error("Telegram send_message raised: %s", exc)
            return False

    async def send_typing_indicator(self, to_number: str) -> None:
        """Send a ``typing`` chat action to show the typing animation.

        Gives the user ~5 seconds of visual feedback before the bot
        reply arrives.  Failures are silently ignored — this is purely
        cosmetic.
        """
        if not config.TELEGRAM_BOT_TOKEN:
            return
        chat_id = to_number.replace("TGID:", "")
        url = f"{TELEGRAM_API}/bot{config.TELEGRAM_BOT_TOKEN}/sendChatAction"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={"chat_id": chat_id, "action": "typing"})
        except Exception:
            pass

    # ── Verification ─────────────────────────────────────────────────────

    def verify_webhook(
        self,
        request_headers: dict,
        request_body: bytes,
        secret: str,
    ) -> bool:
        """Verify the Telegram webhook secret token.

        When the webhook is registered with ``secret_token=…``, Telegram
        includes that exact token in the ``X-Telegram-Bot-Api-Secret-Token``
        header of every request.  A constant-time comparison prevents
        timing attacks.

        If no secret was configured (empty string), verification is
        skipped and True is returned — suitable for development.
        """
        if not secret:
            return True
        header_token = request_headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        return hmac.compare_digest(header_token, secret)

    # ── Formatting ───────────────────────────────────────────────────────

    def format_menu(self, options: list[str], title: str = "") -> str:
        """Format a numbered option list using Telegram MarkdownV2 escaping.

        Periods in numbered items are escaped (``\\.``) as required by
        Telegram's MarkdownV2 parser.  The title is wrapped in ``*bold*``.
        """
        lines: list[str] = []
        if title:
            lines.append(f"*{title}*")
            lines.append("")
        for i, opt in enumerate(options, 1):
            lines.append(f"{i}\\. {opt}")
        return "\n".join(lines)

    def build_inline_keyboard(
        self,
        options: list[str],
        callback_prefix: str = "menu",
    ) -> dict:
        """Build a Telegram ``InlineKeyboardMarkup`` dict.

        Each option becomes a single-button row.  The ``callback_data``
        is ``{prefix}:{index}`` (e.g. ``menu:1``) so the callback query
        handler can identify which item was tapped.

        Pass the returned dict as ``reply_markup`` in a ``ChannelResponse``
        to render buttons below the message.
        """
        buttons = [
            [{"text": f"{i}. {opt}", "callback_data": f"{callback_prefix}:{i}"}]
            for i, opt in enumerate(options, 1)
        ]
        return {"inline_keyboard": buttons}

    # ── Webhook registration ──────────────────────────────────────────────

    async def setup_webhook(
        self,
        webhook_url: str,
        secret_token: str = "",
    ) -> bool:
        """Register the webhook URL with Telegram's ``setWebhook`` API.

        Call this once after deploying or changing the domain.
        ``webhook_url`` must be publicly reachable over HTTPS, e.g.:
            https://your-domain.com/webhook/telegram/default

        Returns True if Telegram acknowledged the request (HTTP 200),
        False otherwise.
        """
        if not config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not set — cannot register webhook")
            return False

        url = f"{TELEGRAM_API}/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook"
        payload: dict = {"url": webhook_url}
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram webhook registered: %s", webhook_url)
                return True
            logger.error(
                "Telegram setWebhook failed [%s]: %s", resp.status_code, resp.text
            )
            return False
        except Exception as exc:
            logger.error("Telegram webhook setup raised: %s", exc)
            return False


# ── Register at module load ───────────────────────────────────────────────

register_channel(TelegramChannel())
