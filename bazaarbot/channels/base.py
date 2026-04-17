"""Abstract channel interface for BazaarBot.

Every channel (WhatsApp, Telegram, SMS, Web, …) subclasses BaseChannel
and implements the three abstract methods. The intent router only ever
sees ChannelMessage / ChannelResponse objects, so adding a new channel
requires no changes to the routing layer.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    WEB = "web"
    API = "api"


@dataclass
class ChannelMessage:
    """Normalised inbound message from any channel.

    Every channel translates its webhook payload into this standard
    format before handing it to the intent router.
    """

    channel: ChannelType
    from_number: str
    text: str
    tenant_slug: str
    raw_payload: dict
    message_id: str | None = None
    media_url: str | None = None
    location: dict | None = None


@dataclass
class ChannelResponse:
    """Response to send back via a channel.

    Build one of these from intent router output and pass it to
    ``channel.send_message()``.
    """

    text: str
    channel: ChannelType
    to_number: str
    media_url: str | None = None
    reply_markup: dict | None = None
    parse_mode: str | None = None


class BaseChannel(ABC):
    """Abstract base class for all BazaarBot channels.

    To add a new channel (e.g. Facebook Messenger):
      1. Subclass BaseChannel
      2. Implement all abstract methods
      3. Register the instance via register_channel()
      4. Add a webhook route in fastapi_app.py

    That's it — no other code changes required.
    """

    @property
    @abstractmethod
    def channel_type(self) -> ChannelType:
        """Returns the ChannelType enum value for this channel."""
        ...

    @abstractmethod
    def parse_incoming(
        self,
        payload: dict,
        tenant_slug: str,
    ) -> ChannelMessage | None:
        """Parse an incoming webhook payload into a ChannelMessage.

        Returns None when the payload should be ignored (e.g. delivery
        receipts, read receipts, or status update callbacks).
        """
        ...

    @abstractmethod
    async def send_message(
        self,
        response: ChannelResponse,
    ) -> bool:
        """Send a message back to the user.

        Returns True on success, False on failure.
        Must never raise — log errors internally.
        """
        ...

    @abstractmethod
    def verify_webhook(
        self,
        request_headers: dict,
        request_body: bytes,
        secret: str,
    ) -> bool:
        """Verify the authenticity of an incoming webhook request.

        Returns True if the signature is valid, False otherwise.
        Twilio uses ``X-Twilio-Signature``; Telegram uses a secret
        token header set during webhook registration.
        """
        ...

    async def send_typing_indicator(self, to_number: str) -> None:
        """Show a typing indicator to the user (optional).

        Override in channels that support it (Telegram supports this;
        Twilio/WhatsApp does not).  Default implementation is a no-op.
        """
        pass

    def format_menu(
        self,
        options: list[str],
        title: str = "",
    ) -> str:
        """Format a numbered option list for this channel.

        WhatsApp uses plain-text numbered lists; Telegram can use inline
        keyboard buttons.  Override in channel subclasses as needed.
        Default: plain numbered text list.
        """
        lines: list[str] = []
        if title:
            lines.append(f"*{title}*")
            lines.append("")
        for i, option in enumerate(options, 1):
            lines.append(f"{i}. {option}")
        return "\n".join(lines)


# ── Channel registry ──────────────────────────────────────────────────────

CHANNEL_REGISTRY: dict[ChannelType, BaseChannel] = {}


def register_channel(channel: BaseChannel) -> None:
    """Register a channel instance in the global registry."""
    CHANNEL_REGISTRY[channel.channel_type] = channel
    logger.debug("Registered channel: %s", channel.channel_type)


def get_channel(channel_type: ChannelType) -> BaseChannel | None:
    """Look up a registered channel by type.  Returns None if not found."""
    return CHANNEL_REGISTRY.get(channel_type)
