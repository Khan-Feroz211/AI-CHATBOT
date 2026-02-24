from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from typing import Any, Dict, Optional

import httpx

from config.settings import settings
from src.api.schemas.whatsapp import WhatsAppSendRequest, WhatsAppSendResponse

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self) -> None:
        self.enabled = settings.WHATSAPP_ENABLED
        self.sandbox = settings.WHATSAPP_SANDBOX_MODE

    def build_outbound_message(self, request: WhatsAppSendRequest) -> WhatsAppSendResponse:
        if not self.enabled:
            return WhatsAppSendResponse(
                success=False,
                status="disabled",
                to_phone=request.to_phone,
                instructions="Set WHATSAPP_ENABLED=true to enable WhatsApp messaging.",
            )

        message_id = self._build_message_id()

        if self.sandbox:
            return WhatsAppSendResponse(
                success=True,
                status="sandbox_queued",
                message_id=message_id,
                to_phone=request.to_phone,
                instructions=(
                    "Sandbox mode: message simulated. For live sending, set WHATSAPP_SANDBOX_MODE=false "
                    "and provide Meta credentials."
                ),
                meta={
                    "sandbox": True,
                    "preview": request.message[:160],
                },
            )

        missing_config = []
        if not settings.WHATSAPP_ACCESS_TOKEN:
            missing_config.append("WHATSAPP_ACCESS_TOKEN")
        if not settings.WHATSAPP_PHONE_NUMBER_ID:
            missing_config.append("WHATSAPP_PHONE_NUMBER_ID")

        if missing_config:
            return WhatsAppSendResponse(
                success=False,
                status="config_missing",
                message_id=message_id,
                to_phone=request.to_phone,
                instructions=f"Set required config: {', '.join(missing_config)}",
                meta={"sandbox": False},
            )

        endpoint = (
            f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": request.to_phone,
            "type": "text",
            "text": {"body": request.message},
        }
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        send_result = self._send_with_retries(endpoint=endpoint, headers=headers, payload=payload)
        if not send_result["success"]:
            logger.error(
                "WhatsApp send failed after retries for phone=%s message_id=%s reason=%s",
                request.to_phone,
                message_id,
                send_result.get("error"),
            )
            return WhatsAppSendResponse(
                success=False,
                status="send_failed",
                message_id=message_id,
                to_phone=request.to_phone,
                instructions="Meta send failed. Check access token, phone ID, and webhook setup.",
                meta={"sandbox": False, "error": send_result.get("error")},
            )

        provider_message_id = send_result.get("provider_message_id")
        logger.info(
            "WhatsApp message sent phone=%s local_message_id=%s provider_message_id=%s attempts=%s",
            request.to_phone,
            message_id,
            provider_message_id,
            send_result.get("attempts"),
        )
        return WhatsAppSendResponse(
            success=True,
            status="sent",
            message_id=provider_message_id or message_id,
            to_phone=request.to_phone,
            instructions="Message sent to Meta WhatsApp API. Track delivery via webhook events.",
            meta={
                "sandbox": False,
                "endpoint": endpoint,
                "attempts": send_result.get("attempts"),
                "local_message_id": message_id,
            },
        )

    def verify_webhook_challenge(
        self, hub_mode: Optional[str], hub_verify_token: Optional[str], hub_challenge: Optional[str]
    ) -> Optional[str]:
        if hub_mode != "subscribe":
            return None
        if not hub_challenge:
            return None
        if not settings.WHATSAPP_VERIFY_TOKEN:
            return None
        if hub_verify_token != settings.WHATSAPP_VERIFY_TOKEN:
            return None
        return hub_challenge

    def verify_webhook_signature(self, body: bytes, signature_header: Optional[str]) -> bool:
        if self.sandbox:
            return True
        if not settings.WHATSAPP_APP_SECRET:
            return False
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_hash = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        actual_hash = signature_header.split("sha256=", 1)[1]
        return hmac.compare_digest(expected_hash, actual_hash)

    def _send_with_retries(self, endpoint: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        attempts = max(1, settings.WHATSAPP_MAX_RETRIES + 1)
        backoff = max(0.0, settings.WHATSAPP_RETRY_BACKOFF_SECONDS)
        timeout = max(5, settings.WHATSAPP_TIMEOUT_SECONDS)

        last_error = "unknown_error"
        for attempt in range(1, attempts + 1):
            try:
                response = self._post_meta_message(
                    endpoint=endpoint,
                    headers=headers,
                    payload=payload,
                    timeout=timeout,
                )
                if response.is_success:
                    response_json = response.json() if response.content else {}
                    provider_message_id = None
                    if isinstance(response_json, dict):
                        messages = response_json.get("messages")
                        if isinstance(messages, list) and messages:
                            first = messages[0]
                            if isinstance(first, dict):
                                provider_message_id = first.get("id")
                    return {
                        "success": True,
                        "provider_message_id": provider_message_id,
                        "attempts": attempt,
                    }

                error_text = response.text[:240] if response.text else f"http_{response.status_code}"
                last_error = f"http_{response.status_code}:{error_text}"
                logger.warning("WhatsApp send attempt=%s failed: %s", attempt, last_error)

            except httpx.HTTPError as exc:
                last_error = f"http_error:{exc.__class__.__name__}"
                logger.warning("WhatsApp send attempt=%s raised %s", attempt, last_error)

            if attempt < attempts and backoff > 0:
                time.sleep(backoff * attempt)

        return {"success": False, "error": last_error, "attempts": attempts}

    @staticmethod
    def _post_meta_message(endpoint: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> httpx.Response:
        with httpx.Client(timeout=timeout) as client:
            return client.post(endpoint, headers=headers, json=payload)

    @staticmethod
    def _build_message_id() -> str:
        return f"wa-{int(time.time())}-{uuid.uuid4().hex[:10]}"
