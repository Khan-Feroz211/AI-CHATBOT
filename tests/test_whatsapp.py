import hashlib
import hmac

from src.api.schemas.whatsapp import WhatsAppSendRequest
from src.services.whatsapp import WhatsAppService


def test_whatsapp_send_sandbox(monkeypatch):
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_ENABLED", True)
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_SANDBOX_MODE", True)

    service = WhatsAppService()
    result = service.build_outbound_message(
        WhatsAppSendRequest(to_phone="923001234567", message="Order confirmed")
    )

    assert result.success is True
    assert result.status == "sandbox_queued"
    assert result.provider == "meta_whatsapp"


def test_whatsapp_webhook_challenge(monkeypatch):
    monkeypatch.setattr(
        "src.services.whatsapp.settings.WHATSAPP_VERIFY_TOKEN", "verify-123"
    )
    service = WhatsAppService()

    ok = service.verify_webhook_challenge("subscribe", "verify-123", "challenge-value")
    bad = service.verify_webhook_challenge("subscribe", "wrong", "challenge-value")

    assert ok == "challenge-value"
    assert bad is None


def test_whatsapp_signature_verification_live(monkeypatch):
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_SANDBOX_MODE", False)
    monkeypatch.setattr(
        "src.services.whatsapp.settings.WHATSAPP_APP_SECRET", "super-secret"
    )

    body = b'{"entry":[{"changes":[]}]}'
    digest = hmac.new(b"super-secret", body, hashlib.sha256).hexdigest()

    service = WhatsAppService()
    assert service.verify_webhook_signature(body, f"sha256={digest}") is True
    assert service.verify_webhook_signature(body, "sha256=bad") is False


def test_whatsapp_send_live_missing_config(monkeypatch):
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_ENABLED", True)
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_SANDBOX_MODE", False)
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_ACCESS_TOKEN", "")
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_PHONE_NUMBER_ID", "")

    service = WhatsAppService()
    result = service.build_outbound_message(
        WhatsAppSendRequest(to_phone="923001234567", message="Order confirmed")
    )

    assert result.success is False
    assert result.status == "config_missing"


def test_whatsapp_send_live_retry_success(monkeypatch):
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_ENABLED", True)
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_SANDBOX_MODE", False)
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_ACCESS_TOKEN", "token")
    monkeypatch.setattr(
        "src.services.whatsapp.settings.WHATSAPP_PHONE_NUMBER_ID", "123456"
    )
    monkeypatch.setattr("src.services.whatsapp.settings.WHATSAPP_MAX_RETRIES", 2)
    monkeypatch.setattr(
        "src.services.whatsapp.settings.WHATSAPP_RETRY_BACKOFF_SECONDS", 0.0
    )

    calls = {"count": 0}

    class FakeResponse:
        def __init__(self, ok: bool):
            self.is_success = ok
            self.status_code = 200 if ok else 500
            self.text = "" if ok else "temporary error"
            self.content = b"{}"

        def json(self):
            return {"messages": [{"id": "wamid-test-123"}]} if self.is_success else {}

    def fake_post(endpoint, headers, payload, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse(False)
        return FakeResponse(True)

    monkeypatch.setattr(WhatsAppService, "_post_meta_message", staticmethod(fake_post))

    service = WhatsAppService()
    result = service.build_outbound_message(
        WhatsAppSendRequest(to_phone="923001234567", message="Retry test")
    )

    assert result.success is True
    assert result.status == "sent"
    assert result.message_id == "wamid-test-123"
    assert calls["count"] == 2
