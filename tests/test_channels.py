"""BazaarBot channel interface tests — Day 5.

All tests use mocking only.  No real Telegram Bot API calls or Twilio
requests are made; external I/O is fully stubbed with unittest.mock.

Run:
    pytest tests/test_channels.py -v
"""
import os
import sys

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Env bootstrap (must be before any bazaarbot import) ───────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "")

# ── Imports ───────────────────────────────────────────────────────────────
from bazaarbot.channels.base import (  # noqa: E402
    ChannelMessage,
    ChannelResponse,
    ChannelType,
    CHANNEL_REGISTRY,
    get_channel,
)
from bazaarbot.channels.whatsapp import WhatsAppChannel  # noqa: E402
from bazaarbot.channels.telegram_channel import TelegramChannel  # noqa: E402
from bazaarbot.channels.web_channel import WebChannel  # noqa: E402
from bazaarbot.bot.channel_router import handle_channel_message  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════
# Channel registry
# ═══════════════════════════════════════════════════════════════════════════

def test_channel_registry_has_all_channels():
    """Importing the channel modules must register all three channels."""
    assert ChannelType.WHATSAPP in CHANNEL_REGISTRY
    assert ChannelType.TELEGRAM in CHANNEL_REGISTRY
    assert ChannelType.WEB in CHANNEL_REGISTRY


def test_get_channel_returns_correct_type():
    """get_channel() must return the registered instance for each type."""
    assert isinstance(get_channel(ChannelType.WHATSAPP), WhatsAppChannel)
    assert isinstance(get_channel(ChannelType.TELEGRAM), TelegramChannel)
    assert isinstance(get_channel(ChannelType.WEB), WebChannel)


def test_get_channel_unknown_returns_none():
    assert get_channel(ChannelType.SMS) is None


# ═══════════════════════════════════════════════════════════════════════════
# WhatsApp channel — parse_incoming
# ═══════════════════════════════════════════════════════════════════════════

class TestWhatsAppParseIncoming:
    def setup_method(self):
        self.channel = WhatsAppChannel()

    def test_valid_payload(self):
        payload = {
            "Body": "stock check karein",
            "From": "whatsapp:+923001234567",
            "To": "whatsapp:+14155238886",
            "MessageSid": "SM123",
        }
        msg = self.channel.parse_incoming(payload, "test-dukan")

        assert msg is not None
        assert msg.channel == ChannelType.WHATSAPP
        assert msg.from_number == "+923001234567"
        assert msg.text == "stock check karein"
        assert msg.tenant_slug == "test-dukan"
        assert msg.message_id == "SM123"

    def test_from_whatsapp_prefix_stripped(self):
        payload = {
            "Body": "hello",
            "From": "whatsapp:+923009999999",
        }
        msg = self.channel.parse_incoming(payload, "default")
        assert msg is not None
        assert msg.from_number == "+923009999999"

    def test_empty_body_returns_none(self):
        """Only when both Body AND From are absent should the result be None.

        The WhatsApp implementation returns None only when *both* body and
        from_raw are falsy.  An empty Body with a valid From produces a
        ChannelMessage with text="" so the intent router can still respond.
        """
        payload = {}   # both Body and From missing
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_empty_from_returns_none(self):
        """Same rule: both fields absent → None."""
        # body present, From absent → ChannelMessage is returned (From="" accepted)
        payload_with_body = {"Body": "hello"}
        msg = self.channel.parse_incoming(payload_with_body, "test")
        assert msg is not None   # body alone is sufficient

        # Completely empty payload → None
        msg_empty = self.channel.parse_incoming({}, "test")
        assert msg_empty is None

    def test_media_url_captured(self):
        payload = {
            "Body": "image received",
            "From": "whatsapp:+923001234567",
            "MediaUrl0": "https://api.twilio.com/img/photo.jpg",
        }
        msg = self.channel.parse_incoming(payload, "default")
        assert msg is not None
        assert msg.media_url == "https://api.twilio.com/img/photo.jpg"


# ═══════════════════════════════════════════════════════════════════════════
# Telegram channel — parse_incoming
# ═══════════════════════════════════════════════════════════════════════════

def _tg_payload(text: str, chat_id: int = 987654321) -> dict:
    """Build a minimal Telegram webhook update dict."""
    return {
        "update_id": 12345,
        "message": {
            "message_id": 1,
            "from": {"id": chat_id, "first_name": "Ali"},
            "chat": {"id": chat_id, "type": "private"},
            "text": text,
        },
    }


class TestTelegramParseIncoming:
    def setup_method(self):
        self.channel = TelegramChannel()

    def test_text_message(self):
        msg = self.channel.parse_incoming(
            _tg_payload("payment kaise karein"), "test-dukan"
        )
        assert msg is not None
        assert msg.channel == ChannelType.TELEGRAM
        assert msg.from_number == "TGID:987654321"
        assert msg.text == "payment kaise karein"
        assert msg.tenant_slug == "test-dukan"

    def test_start_command_maps_to_hello(self):
        msg = self.channel.parse_incoming(_tg_payload("/start"), "test")
        assert msg is not None
        assert msg.text == "hello"

    def test_help_command_maps(self):
        msg = self.channel.parse_incoming(_tg_payload("/help"), "test")
        assert msg is not None
        assert msg.text == "help"

    def test_stock_command_maps(self):
        msg = self.channel.parse_incoming(_tg_payload("/stock"), "test")
        assert msg is not None
        assert msg.text == "stock"

    def test_order_command_with_args(self):
        msg = self.channel.parse_incoming(_tg_payload("/order rice 5"), "test")
        assert msg is not None
        assert msg.text == "order rice 5"

    def test_order_command_bare(self):
        msg = self.channel.parse_incoming(_tg_payload("/order"), "test")
        assert msg is not None
        assert msg.text == "order"

    def test_no_message_key_returns_none(self):
        payload = {"update_id": 12345}
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_edited_message_returns_none(self):
        payload = {
            "update_id": 12345,
            "edited_message": {"message_id": 1, "text": "edited"},
        }
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_channel_post_returns_none(self):
        payload = {
            "update_id": 12345,
            "channel_post": {"message_id": 1, "text": "broadcast"},
        }
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_no_text_returns_none(self):
        """Sticker / voice / photo updates have no text — should be ignored."""
        payload = {
            "update_id": 12345,
            "message": {
                "message_id": 1,
                "chat": {"id": 1, "type": "private"},
                "sticker": {"file_id": "abc"},
            },
        }
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_missing_chat_key_returns_none(self):
        """A message dict without 'chat' should not raise and return None."""
        payload = {
            "update_id": 12345,
            "message": {"message_id": 1, "text": "hi"},
        }
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_missing_chat_id_returns_none(self):
        payload = {
            "update_id": 12345,
            "message": {"message_id": 1, "chat": {}, "text": "hi"},
        }
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_from_number_format(self):
        msg = self.channel.parse_incoming(_tg_payload("hi", chat_id=111222333), "test")
        assert msg is not None
        assert msg.from_number == "TGID:111222333"

    def test_unknown_command_forwarded(self):
        msg = self.channel.parse_incoming(_tg_payload("/mycommand hello"), "test")
        assert msg is not None
        assert msg.text == "mycommand hello"


# ═══════════════════════════════════════════════════════════════════════════
# Web channel — parse_incoming
# ═══════════════════════════════════════════════════════════════════════════

class TestWebChannelParseIncoming:
    def setup_method(self):
        self.channel = WebChannel()

    def test_valid_payload(self):
        payload = {"message": "hello", "phone": "+923001234567"}
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is not None
        assert msg.text == "hello"
        assert msg.from_number == "+923001234567"
        assert msg.channel == ChannelType.WEB

    def test_missing_phone_defaults_to_web_user(self):
        payload = {"message": "hi"}
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is not None
        assert msg.from_number == "web_user"

    def test_empty_message_returns_none(self):
        payload = {"message": "", "phone": "+923001"}
        msg = self.channel.parse_incoming(payload, "test")
        assert msg is None

    def test_missing_message_returns_none(self):
        msg = self.channel.parse_incoming({}, "test")
        assert msg is None


# ═══════════════════════════════════════════════════════════════════════════
# WhatsApp channel — verify_webhook
# ═══════════════════════════════════════════════════════════════════════════

class TestWhatsAppVerifyWebhook:
    def setup_method(self):
        self.channel = WhatsAppChannel()

    def test_development_mode_skips_check(self):
        with patch("bazaarbot.channels.whatsapp.config") as mock_cfg:
            mock_cfg.APP_ENV = "development"
            result = self.channel.verify_webhook({}, b"body", "secret")
        assert result is True

    def test_production_invalid_signature(self):
        with patch("bazaarbot.channels.whatsapp.config") as mock_cfg:
            mock_cfg.APP_ENV = "production"
            # No real Twilio RequestValidator — validation will fail gracefully
            result = self.channel.verify_webhook(
                {"X-Twilio-Signature": "bad", "X-Original-URL": "https://x.com"},
                b"Body=hi",
                "secret",
            )
        # Returns False rather than raising when signature doesn't match
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# Telegram channel — send_message
# ═══════════════════════════════════════════════════════════════════════════

class TestTelegramSendMessage:
    def setup_method(self):
        self.channel = TelegramChannel()
        self.response = ChannelResponse(
            text="Test reply",
            channel=ChannelType.TELEGRAM,
            to_number="TGID:987654321",
        )

    @pytest.mark.asyncio
    async def test_send_returns_true_on_200(self):
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient", return_value=mock_client):
            mock_cfg.TELEGRAM_BOT_TOKEN = "test-token"
            result = await self.channel.send_message(self.response)

        assert result is True
        mock_client.post.assert_awaited_once()
        call_kwargs = mock_client.post.call_args
        assert "bot{}/sendMessage".format("test-token") in call_kwargs[0][0]

    @pytest.mark.asyncio
    async def test_send_returns_false_on_non_200(self):
        mock_http_response = MagicMock()
        mock_http_response.status_code = 400
        mock_http_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient", return_value=mock_client):
            mock_cfg.TELEGRAM_BOT_TOKEN = "test-token"
            result = await self.channel.send_message(self.response)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_without_token_returns_false(self):
        """Empty TELEGRAM_BOT_TOKEN must return False without making HTTP calls."""
        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient") as mock_client_cls:
            mock_cfg.TELEGRAM_BOT_TOKEN = ""
            result = await self.channel.send_message(self.response)

        assert result is False
        mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_graceful_on_network_error(self):
        """A network exception must be caught and return False."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient", return_value=mock_client):
            mock_cfg.TELEGRAM_BOT_TOKEN = "test-token"
            result = await self.channel.send_message(self.response)

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# Telegram channel — send_typing_indicator
# ═══════════════════════════════════════════════════════════════════════════

class TestTelegramTypingIndicator:
    def setup_method(self):
        self.channel = TelegramChannel()

    @pytest.mark.asyncio
    async def test_typing_sent_when_token_set(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient", return_value=mock_client):
            mock_cfg.TELEGRAM_BOT_TOKEN = "tok"
            await self.channel.send_typing_indicator("TGID:123")

        mock_client.post.assert_awaited_once()
        payload_sent = mock_client.post.call_args[1]["json"]
        assert payload_sent["chat_id"] == "123"
        assert payload_sent["action"] == "typing"

    @pytest.mark.asyncio
    async def test_typing_skipped_without_token(self):
        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient") as mock_cls:
            mock_cfg.TELEGRAM_BOT_TOKEN = ""
            await self.channel.send_typing_indicator("TGID:123")

        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_does_not_raise_on_error(self):
        """Network failure in typing indicator must be silently swallowed."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bazaarbot.channels.telegram_channel.config") as mock_cfg, \
             patch("httpx.AsyncClient", return_value=mock_client):
            mock_cfg.TELEGRAM_BOT_TOKEN = "tok"
            # Must not raise
            await self.channel.send_typing_indicator("TGID:123")


# ═══════════════════════════════════════════════════════════════════════════
# Web channel — send_message (no-op)
# ═══════════════════════════════════════════════════════════════════════════

class TestWebChannelSendMessage:
    @pytest.mark.asyncio
    async def test_send_always_returns_true(self):
        channel = WebChannel()
        response = ChannelResponse(
            text="hi there",
            channel=ChannelType.WEB,
            to_number="web_user",
        )
        assert await channel.send_message(response) is True


# ═══════════════════════════════════════════════════════════════════════════
# handle_channel_message — WhatsApp
# ═══════════════════════════════════════════════════════════════════════════

class TestHandleChannelMessageWhatsApp:
    @pytest.mark.asyncio
    async def test_returns_correct_response(self):
        msg = ChannelMessage(
            channel=ChannelType.WHATSAPP,
            from_number="+923001234567",
            text="hello",
            tenant_slug="test-dukan",
            raw_payload={},
        )

        with patch(
            "bazaarbot.bot.channel_router.process_message",
            return_value="Shukriya!",
        ) as mock_pm, patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            get_channel(ChannelType.WHATSAPP),
            "send_message",
            new_callable=AsyncMock,
            return_value=True,
        ):
            mock_cfg.USE_LLM_FALLBACK = False
            response = await handle_channel_message(msg)

        assert response.text == "Shukriya!"
        assert response.channel == ChannelType.WHATSAPP
        assert response.to_number == "+923001234567"
        mock_pm.assert_called_once_with(
            phone="+923001234567",
            message="hello",
            tenant_slug="test-dukan",
        )

    @pytest.mark.asyncio
    async def test_send_failure_is_logged_not_raised(self):
        msg = ChannelMessage(
            channel=ChannelType.WHATSAPP,
            from_number="+923001234567",
            text="stock",
            tenant_slug="default",
            raw_payload={},
        )

        with patch(
            "bazaarbot.bot.channel_router.process_message",
            return_value="Aapka stock!",
        ), patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            get_channel(ChannelType.WHATSAPP),
            "send_message",
            new_callable=AsyncMock,
            return_value=False,          # simulate delivery failure
        ):
            mock_cfg.USE_LLM_FALLBACK = False
            # Must not raise even when send fails
            response = await handle_channel_message(msg)

        assert response.text == "Aapka stock!"


# ═══════════════════════════════════════════════════════════════════════════
# handle_channel_message — Telegram
# ═══════════════════════════════════════════════════════════════════════════

class TestHandleChannelMessageTelegram:
    @pytest.mark.asyncio
    async def test_typing_indicator_called(self):
        msg = ChannelMessage(
            channel=ChannelType.TELEGRAM,
            from_number="TGID:987654321",
            text="payment kaise karein",
            tenant_slug="test-dukan",
            raw_payload={},
        )

        telegram_ch = get_channel(ChannelType.TELEGRAM)

        with patch(
            "bazaarbot.bot.channel_router.process_message",
            return_value="Payment info here.",
        ), patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            telegram_ch,
            "send_typing_indicator",
            new_callable=AsyncMock,
        ) as mock_typing, patch.object(
            telegram_ch,
            "send_message",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            mock_cfg.USE_LLM_FALLBACK = False
            response = await handle_channel_message(msg)

        mock_typing.assert_awaited_once_with("TGID:987654321")
        mock_send.assert_awaited_once()
        assert response.channel == ChannelType.TELEGRAM
        assert response.to_number == "TGID:987654321"

    @pytest.mark.asyncio
    async def test_llm_fallback_uses_async_router(self):
        msg = ChannelMessage(
            channel=ChannelType.TELEGRAM,
            from_number="TGID:111",
            text="help",
            tenant_slug="default",
            raw_payload={},
        )

        telegram_ch = get_channel(ChannelType.TELEGRAM)

        with patch(
            "bazaarbot.bot.channel_router.process_message_async",
            new_callable=AsyncMock,
            return_value="LLM reply",
        ) as mock_async, patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            telegram_ch, "send_typing_indicator", new_callable=AsyncMock
        ), patch.object(
            telegram_ch, "send_message", new_callable=AsyncMock, return_value=True
        ):
            mock_cfg.USE_LLM_FALLBACK = True
            response = await handle_channel_message(msg)

        mock_async.assert_awaited_once_with(
            message="help",
            phone="TGID:111",
            tenant_slug="default",
            channel="telegram",
        )
        assert response.text == "LLM reply"


# ═══════════════════════════════════════════════════════════════════════════
# handle_channel_message — unknown channel
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_handle_channel_message_unknown_channel():
    """An unregistered channel must return a graceful error response."""
    msg = ChannelMessage(
        channel=ChannelType.SMS,   # SMS is not registered
        from_number="+923001234567",
        text="hello",
        tenant_slug="default",
        raw_payload={},
    )
    response = await handle_channel_message(msg)
    assert response.text == "Service unavailable"
    assert response.to_number == "+923001234567"


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI /webhook route (WhatsApp integration)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def fastapi_client():
    """Create a FastAPI test client with mocked DB and channel sends.

    Scope is module-level to avoid re-importing heavy dependencies for
    every test function.
    """
    from fastapi.testclient import TestClient

    with patch("bazaarbot.database.init_db"), \
         patch("bazaarbot.database.log_message"), \
         patch("bazaarbot.database.get_session", return_value={"state": "idle"}), \
         patch("bazaarbot.database.get_tenant", return_value={"name": "TestShop"}):
        from bazaarbot.web.fastapi_app import app
        client = TestClient(app, raise_server_exceptions=False)
        yield client


class TestWhatsAppWebhookRoute:
    def test_get_webhook_returns_ok(self, fastapi_client):
        r = fastapi_client.get("/webhook")
        assert r.status_code == 200

    def test_post_webhook_hi_returns_xml(self, fastapi_client):
        """POST with a greeting must return a 200 with XML content-type."""
        with patch(
            "bazaarbot.bot.channel_router.process_message",
            return_value="BazaarBot mein khush aamdeed!",
        ), patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            get_channel(ChannelType.WHATSAPP),
            "send_message",
            new_callable=AsyncMock,
            return_value=True,
        ):
            mock_cfg.USE_LLM_FALLBACK = False
            r = fastapi_client.post(
                "/webhook",
                data={
                    "Body": "hi",
                    "From": "whatsapp:+923000000000",
                    "To": "whatsapp:+14155238886",
                },
            )

        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "").lower()

    def test_post_webhook_empty_body_returns_xml(self, fastapi_client):
        """Delivery receipt (no Body/From) must return empty TwiML silently."""
        r = fastapi_client.post("/webhook", data={})
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "").lower()

    def test_get_webhook_hub_challenge(self, fastapi_client):
        """Meta-style hub challenge must echo back the challenge integer."""
        import bazaarbot.config as cfg_mod
        cfg_mod.config.WEBHOOK_VERIFY_TOKEN = "hub-secret"
        r = fastapi_client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "hub-secret",
                "hub.challenge": "9876543210",
            },
        )
        assert r.status_code == 200
        assert b"9876543210" in r.content

    def test_get_webhook_hub_challenge_wrong_token(self, fastapi_client):
        import bazaarbot.config as cfg_mod
        cfg_mod.config.WEBHOOK_VERIFY_TOKEN = "hub-secret"
        r = fastapi_client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "1234",
            },
        )
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# Telegram webhook route
# ═══════════════════════════════════════════════════════════════════════════

class TestTelegramWebhookRoute:
    def test_post_telegram_webhook_valid(self, fastapi_client):
        """A valid Telegram update with no secret token must return 200."""
        import bazaarbot.config as cfg_mod
        cfg_mod.config.TELEGRAM_WEBHOOK_SECRET = ""   # no secret in tests

        payload = {
            "update_id": 99,
            "message": {
                "message_id": 1,
                "from": {"id": 12345, "first_name": "Test"},
                "chat": {"id": 12345, "type": "private"},
                "text": "hi",
            },
        }

        with patch(
            "bazaarbot.bot.channel_router.process_message",
            return_value="Marhaba!",
        ), patch(
            "bazaarbot.bot.channel_router.Config",
        ) as mock_cfg, patch.object(
            get_channel(ChannelType.TELEGRAM),
            "send_message",
            new_callable=AsyncMock,
            return_value=True,
        ), patch.object(
            get_channel(ChannelType.TELEGRAM),
            "send_typing_indicator",
            new_callable=AsyncMock,
        ):
            mock_cfg.USE_LLM_FALLBACK = False
            r = fastapi_client.post(
                "/webhook/telegram/test-dukan",
                json=payload,
            )

        assert r.status_code == 200

    def test_post_telegram_webhook_invalid_slug(self, fastapi_client):
        r = fastapi_client.post(
            "/webhook/telegram/../../etc/passwd",
            json={"update_id": 1},
        )
        assert r.status_code in (400, 404)

    def test_post_telegram_webhook_wrong_secret(self, fastapi_client):
        import bazaarbot.config as cfg_mod
        cfg_mod.config.TELEGRAM_WEBHOOK_SECRET = "correct-secret"

        r = fastapi_client.post(
            "/webhook/telegram/default",
            json={"update_id": 1, "message": {"text": "hi", "chat": {"id": 1}}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert r.status_code == 403
