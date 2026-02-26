import hmac
import hashlib
import importlib
import os
import json
import types
import pytest


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "token")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-token")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret")

    # Reload module to pick env vars
    module = importlib.reload(importlib.import_module("whatsapp_bot.app"))
    return module.app


def sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_success(app):
    client = app.test_client()
    res = client.get("/webhook?hub.verify_token=verify-token&hub.challenge=123")
    assert res.status_code == 200
    assert res.data == b"123"


def test_verify_failure_logged(app, caplog):
    client = app.test_client()
    res = client.get("/webhook?hub.verify_token=bad&hub.challenge=123")
    assert res.status_code == 403
    assert any("verify_failed" in rec.message for rec in caplog.records)


def test_inbound_happy_path(app, monkeypatch):
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=0):
        sent["payload"] = json
        return types.SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr("requests.post", fake_post)

    client = app.test_client()
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"id": "m1", "from": "111", "text": {"body": "book meeting"}}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode()
    res = client.post(
        "/webhook",
        data=body,
        headers={"X-Hub-Signature-256": sign(body, "secret"), "Content-Type": "application/json"},
    )
    assert res.status_code == 200
    assert sent["payload"]["text"]["body"].startswith("Share date/time")


def test_inbound_unknown_message(app, monkeypatch):
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=0):
        sent["payload"] = json
        return types.SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr("requests.post", fake_post)

    client = app.test_client()
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"id": "m2", "from": "111", "text": {"body": "hello there"}}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode()
    res = client.post(
        "/webhook",
        data=body,
        headers={"X-Hub-Signature-256": sign(body, "secret"), "Content-Type": "application/json"},
    )
    assert res.status_code == 200
    assert "bookings" in sent["payload"]["text"]["body"]


def test_signature_invalid(app):
    client = app.test_client()
    payload = {"entry": []}
    body = json.dumps(payload).encode()
    res = client.post(
        "/webhook",
        data=body,
        headers={"X-Hub-Signature-256": "sha256=deadbeef", "Content-Type": "application/json"},
    )
    assert res.status_code == 403
