"""Channels package — abstract interface plus WhatsApp, Web, and Email."""

from bazaarbot.channels.base import (
    BaseChannel,
    ChannelMessage,
    ChannelResponse,
    ChannelType,
    CHANNEL_REGISTRY,
    get_channel,
    register_channel,
)

# Import channel implementations so their register_channel() calls run at
# package-import time.  Email keeps its own standalone helpers and does not
# implement BaseChannel (it is not a two-way interactive channel).
from bazaarbot.channels import whatsapp, web_channel, telegram_channel  # noqa: F401

__all__ = [
    "BaseChannel",
    "ChannelMessage",
    "ChannelResponse",
    "ChannelType",
    "CHANNEL_REGISTRY",
    "get_channel",
    "register_channel",
]
