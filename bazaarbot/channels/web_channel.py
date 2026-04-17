"""Web chat widget channel for BazaarBot.

Handles the POST /chat endpoint used by the embedded web chat widget.
Unlike push-based channels (WhatsApp, Telegram), the web channel is
request/response: the HTTP response *is* the outbound message, so
``send_message`` is intentionally a no-op.
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

logger = logging.getLogger(__name__)


class WebChannel(BaseChannel):
    """HTTP-based web chat widget channel."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.WEB

    def parse_incoming(
        self,
        payload: dict,
        tenant_slug: str,
    ) -> ChannelMessage | None:
        """Parse a web chat widget JSON payload into a ChannelMessage.

        Expected fields:
          message  (str, required) — the user's text
          phone    (str, optional) — caller identifier; defaults to
                                     ``"web_user"`` when absent

        Returns None when the message text is empty.
        """
        text = payload.get("message", "").strip()
        if not text:
            return None
        return ChannelMessage(
            channel=ChannelType.WEB,
            from_number=payload.get("phone", "web_user"),
            text=text,
            tenant_slug=tenant_slug,
            raw_payload=payload,
        )

    async def send_message(self, response: ChannelResponse) -> bool:
        """No-op: for the web channel the HTTP response carries the reply.

        The FastAPI ``/chat`` route returns the bot's reply directly in
        the JSON response body, so there is nothing to push here.
        Always returns True.
        """
        return True

    def verify_webhook(
        self,
        request_headers: dict,
        request_body: bytes,
        secret: str,
    ) -> bool:
        """Web requests originate from the same origin — always valid."""
        return True


# ── Register at module load ───────────────────────────────────────────────

register_channel(WebChannel())
