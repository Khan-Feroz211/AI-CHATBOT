import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional

import requests
from flask import Flask, jsonify, request

try:
    import redis  # optional
except ImportError:  # pragma: no cover
    redis = None

app = Flask(__name__)

# Required environment variables (no secrets in code)
PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID") or os.environ["WHATSAPP_PHONE_NUMBER_ID"]
ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]
APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")

API_ROOT = f"https://graph.facebook.com/v20.0/{PHONE_ID}"
TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_BASE = 0.5
MAX_MESSAGES_PER_MIN = int(os.environ.get("RATE_LIMIT_PER_MIN", "6"))
PROCESSED_CACHE_LIMIT = 512
REDIS_URL = os.environ.get("REDIS_URL")

logger = logging.getLogger("whatsapp_bot")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

# In-memory controls (sufficient for demo; swap to Redis in prod)
processed_ids = deque(maxlen=PROCESSED_CACHE_LIMIT)
rate_window = defaultdict(lambda: {"ts": 0, "count": 0})
redis_client: Optional["redis.Redis"] = None
if REDIS_URL and redis is not None:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
        logger.info("redis_enabled", extra={"url": REDIS_URL})
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_unavailable_fallback_memory", extra={"error": str(exc)})
        redis_client = None


def _post_with_retry(
    url: str, headers: Dict[str, str], payload: Dict[str, Any]
) -> requests.Response:
    """POST with exponential backoff."""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code < 500:
                return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        sleep_for = BACKOFF_BASE * (2 ** (attempt - 1))
        logger.warning("post_retry", extra={"attempt": attempt, "sleep": sleep_for})
        time.sleep(sleep_for)
    if last_exc:
        raise last_exc
    return resp  # type: ignore[misc]


def send_text(to: str, body: str) -> None:
    """Send a simple text message via WhatsApp Cloud API with retries."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    resp = _post_with_retry(f"{API_ROOT}/messages", headers, payload)
    if resp.status_code >= 300:
        logger.error(
            "send_text_failed", extra={"status": resp.status_code, "body": resp.text}
        )


def _valid_signature(raw_body: bytes, header_sig: str) -> bool:
    if not APP_SECRET or not header_sig:
        return False
    expected = (
        "sha256="
        + hmac.new(
            APP_SECRET.encode(), msg=raw_body, digestmod=hashlib.sha256
        ).hexdigest()
    )
    return hmac.compare_digest(expected, header_sig)


def _rate_limited(sender: str) -> bool:
    if redis_client:
        key = f"rl:{sender}"
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)
        return count > MAX_MESSAGES_PER_MIN
    now = int(time.time())
    bucket = rate_window[sender]
    if now - bucket["ts"] >= 60:
        bucket["ts"] = now
        bucket["count"] = 0
    bucket["count"] += 1
    return bucket["count"] > MAX_MESSAGES_PER_MIN


def _seen_message(msg_id: str) -> bool:
    if redis_client:
        key = f"msg:{msg_id}"
        added = redis_client.set(key, 1, nx=True, ex=24 * 3600)
        return added is None
    if msg_id in processed_ids:
        return True
    processed_ids.append(msg_id)
    return False


@app.get("/webhook")
def verify() -> Any:
    """Meta challenge endpoint."""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if token == VERIFY_TOKEN:
        logger.info("verify_ok")
        return challenge
    logger.warning("verify_failed", extra={"token": token})
    return "forbidden", 403


@app.post("/webhook")
def inbound():
    """Handle inbound WhatsApp messages."""
    raw_body = request.get_data()
    header_sig = request.headers.get("X-Hub-Signature-256", "")
    if APP_SECRET and not _valid_signature(raw_body, header_sig):
        logger.warning("signature_invalid")
        return "invalid signature", 403

    data = request.get_json(silent=True) or {}

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                msg_id = msg.get("id")
                sender = msg.get("from")
                text = (msg.get("text", {}) or {}).get("body", "").lower()

                if not sender or not msg_id:
                    continue

                if _seen_message(msg_id):
                    logger.info("duplicate_message_ignored", extra={"msg_id": msg_id})
                    continue

                if _rate_limited(sender):
                    logger.warning("rate_limited", extra={"sender": sender})
                    continue

                if text.startswith("book"):
                    send_text(
                        sender,
                        "Share date/time + meeting title; I’ll book and confirm.",
                    )
                elif text.startswith("sponsor"):
                    send_text(
                        sender,
                        "Send sponsor budget, timeline, and contact email; I’ll log and confirm.",
                    )
                else:
                    send_text(
                        sender,
                        "Hi! I handle sponsor inquiries and meeting bookings. Reply 'book' or 'sponsor'.",
                    )

    return jsonify(status="ok")


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.get("/")
def root():
    return jsonify(status="ok", endpoints=["/healthz", "/webhook"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
