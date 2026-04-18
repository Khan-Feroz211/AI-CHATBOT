"""Unified channel message handler for BazaarBot.

This module provides a single entry point — ``handle_channel_message`` —
that processes an incoming ``ChannelMessage`` through the intent router
and sends the reply back via the originating channel.

All channel-specific routing logic (WhatsApp, Telegram, Web) is handled
here so FastAPI webhook routes stay thin: they only parse the HTTP request
and call ``handle_channel_message``.
"""
from __future__ import annotations

import logging

from bazaarbot.bot.intent_router import process_message, process_message_async
from bazaarbot.channels.base import ChannelMessage, ChannelResponse, get_channel
from bazaarbot.config import Config

logger = logging.getLogger(__name__)


async def handle_channel_message(
    msg: ChannelMessage,
) -> ChannelResponse:
    """Unified handler for messages from any channel.

    Steps:
      1. Look up the channel implementation in the registry.
      2. Show a typing indicator (no-op on channels that don't support it).
      3. Route the message through the intent router (async when
         ``USE_LLM_FALLBACK`` is True, sync otherwise).
      4. Send the reply back through the same channel.
      5. Return the ``ChannelResponse`` so callers can log or inspect it.

    This is the **single entry point** for all incoming messages regardless
    of channel.  Adding a new channel never requires changes here.
    """
    channel = get_channel(msg.channel)
    if not channel:
        logger.error("No handler registered for channel: %s", msg.channel)
        return ChannelResponse(
            text="Service unavailable",
            channel=msg.channel,
            to_number=msg.from_number,
        )

    # Show typing animation while we process (Telegram; no-op elsewhere)
    await channel.send_typing_indicator(msg.from_number)

    # Check whether the tenant's subscription plan permits LLM fallback.
    # Business and Pro plans have llm_enabled=True; Starter and free-trial
    # tenants fall back to the TF-IDF engine regardless of USE_LLM_FALLBACK.
    llm_allowed = False
    if Config.USE_LLM_FALLBACK:
        try:
            from bazaarbot.billing.middleware import check_llm_access
            from bazaarbot.database_pg import AsyncSessionLocal

            async with AsyncSessionLocal() as _db:
                llm_allowed = await check_llm_access(msg.tenant_slug, _db)
        except Exception as _exc:
            logger.warning(
                "LLM access check failed for tenant=%s: %s — falling back to TF-IDF",
                msg.tenant_slug,
                _exc,
            )

    # Route through intent engine
    if Config.USE_LLM_FALLBACK and llm_allowed:
        reply = await process_message_async(
            message=msg.text,
            phone=msg.from_number,
            tenant_slug=msg.tenant_slug,
            channel=msg.channel.value,
        )
    else:
        reply = process_message(
            phone=msg.from_number,
            message=msg.text,
            tenant_slug=msg.tenant_slug,
        )

    response = ChannelResponse(
        text=reply,
        channel=msg.channel,
        to_number=msg.from_number,
    )

    # Push reply to the user via the channel's transport
    success = await channel.send_message(response)
    if not success:
        logger.warning(
            "Failed to deliver reply via %s to %s",
            msg.channel.value,
            msg.from_number,
        )

    return response
