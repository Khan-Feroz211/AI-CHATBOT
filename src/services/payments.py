from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from typing import Dict

from config.settings import settings
from src.api.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentProvider,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)


class PaymentService:
    def __init__(self) -> None:
        self.sandbox = settings.PAYMENT_SANDBOX_MODE

    def create_payment(self, request: PaymentCreateRequest) -> PaymentCreateResponse:
        if request.payment_provider == PaymentProvider.jazzcash:
            return self._create_jazzcash_payment(request)
        if request.payment_provider == PaymentProvider.easypaisa:
            return self._create_easypaisa_payment(request)
        if request.payment_provider == PaymentProvider.bank_transfer:
            return self._create_bank_transfer_payment(request)
        if request.payment_provider == PaymentProvider.cod:
            return self._create_cod_payment(request)

        raise ValueError(f"Unsupported payment provider: {request.payment_provider}")

    def handle_webhook(self, request: PaymentWebhookRequest) -> PaymentWebhookResponse:
        verified = self._verify_signature(request)
        if not verified:
            return PaymentWebhookResponse(
                accepted=False,
                verified=False,
                message="Invalid signature for webhook payload",
            )
        return PaymentWebhookResponse(
            accepted=True,
            verified=True,
            message=f"Webhook accepted for {request.provider.value} ({request.reference_id})",
        )

    def _create_jazzcash_payment(
        self, request: PaymentCreateRequest
    ) -> PaymentCreateResponse:
        reference = self._build_reference("JC", request.order_id)
        if self.sandbox:
            return PaymentCreateResponse(
                success=True,
                provider=PaymentProvider.jazzcash,
                status="sandbox_created",
                reference_id=reference,
                checkout_url=f"https://sandbox.local/jazzcash/checkout/{reference}",
                instructions=(
                    "Sandbox payment created. In production, redirect this to JazzCash hosted checkout "
                    "or call JazzCash API server-to-server."
                ),
                message="JazzCash sandbox payment initialized",
                meta={"sandbox": True, "amount_pkr": request.amount_pkr},
            )

        if not settings.JAZZCASH_MERCHANT_ID or not settings.JAZZCASH_INTEGRITY_SALT:
            return PaymentCreateResponse(
                success=False,
                provider=PaymentProvider.jazzcash,
                status="config_missing",
                reference_id=reference,
                instructions="Set JAZZCASH_MERCHANT_ID and JAZZCASH_INTEGRITY_SALT to enable live mode.",
                message="JazzCash live configuration missing",
                meta={"sandbox": False},
            )

        return PaymentCreateResponse(
            success=True,
            provider=PaymentProvider.jazzcash,
            status="ready_for_gateway_call",
            reference_id=reference,
            instructions="Live JazzCash flow ready. Implement final request signing + gateway call per merchant docs.",
            message="JazzCash request prepared",
            meta={"sandbox": False, "merchant_id": settings.JAZZCASH_MERCHANT_ID},
        )

    def _create_easypaisa_payment(
        self, request: PaymentCreateRequest
    ) -> PaymentCreateResponse:
        reference = self._build_reference("EP", request.order_id)
        if self.sandbox:
            return PaymentCreateResponse(
                success=True,
                provider=PaymentProvider.easypaisa,
                status="sandbox_created",
                reference_id=reference,
                checkout_url=f"https://sandbox.local/easypaisa/checkout/{reference}",
                instructions=(
                    "Sandbox payment created. In production, redirect to EasyPaisa checkout "
                    "or submit API transaction request with merchant credentials."
                ),
                message="EasyPaisa sandbox payment initialized",
                meta={"sandbox": True, "amount_pkr": request.amount_pkr},
            )

        if not settings.EASYPAISA_STORE_ID or not settings.EASYPAISA_HASH_KEY:
            return PaymentCreateResponse(
                success=False,
                provider=PaymentProvider.easypaisa,
                status="config_missing",
                reference_id=reference,
                instructions="Set EASYPAISA_STORE_ID and EASYPAISA_HASH_KEY to enable live mode.",
                message="EasyPaisa live configuration missing",
                meta={"sandbox": False},
            )

        return PaymentCreateResponse(
            success=True,
            provider=PaymentProvider.easypaisa,
            status="ready_for_gateway_call",
            reference_id=reference,
            instructions="Live EasyPaisa flow ready. Implement final request payload and hash validation per merchant docs.",
            message="EasyPaisa request prepared",
            meta={"sandbox": False, "store_id": settings.EASYPAISA_STORE_ID},
        )

    def _create_bank_transfer_payment(
        self, request: PaymentCreateRequest
    ) -> PaymentCreateResponse:
        reference = self._build_reference("BT", request.order_id)
        bank_name = settings.BANK_TRANSFER_BANK_NAME or "Your Bank"
        account_title = settings.BANK_TRANSFER_ACCOUNT_TITLE or "Your Business Account"
        iban = settings.BANK_TRANSFER_IBAN or "PK00XXXX0000000000000000"
        return PaymentCreateResponse(
            success=True,
            provider=PaymentProvider.bank_transfer,
            status="instructions_generated",
            reference_id=reference,
            instructions=(
                f"Transfer PKR {request.amount_pkr:.2f} to {bank_name} ({account_title}) IBAN: {iban}. "
                f"Use reference {reference} and share payment screenshot on WhatsApp."
            ),
            message="Bank transfer instructions generated",
        )

    def _create_cod_payment(
        self, request: PaymentCreateRequest
    ) -> PaymentCreateResponse:
        reference = self._build_reference("COD", request.order_id)
        return PaymentCreateResponse(
            success=True,
            provider=PaymentProvider.cod,
            status="marked_cod",
            reference_id=reference,
            instructions=(
                f"Cash on Delivery for PKR {request.amount_pkr:.2f}. "
                "Collect cash on delivery and mark payment as received after handover."
            ),
            message="COD order marked",
        )

    def _verify_signature(self, request: PaymentWebhookRequest) -> bool:
        # Sandbox mode accepts webhook payloads for easier local testing.
        if self.sandbox:
            return True

        secret = self._provider_webhook_secret(request.provider)
        if not secret or not request.signature:
            return False

        payload = (
            f"{request.reference_id}|{request.status}|{request.amount_pkr or 0}".encode(
                "utf-8"
            )
        )
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, request.signature)

    def _provider_webhook_secret(self, provider: PaymentProvider) -> str:
        if provider == PaymentProvider.jazzcash:
            return settings.JAZZCASH_WEBHOOK_SECRET or settings.JAZZCASH_INTEGRITY_SALT
        if provider == PaymentProvider.easypaisa:
            return settings.EASYPAISA_WEBHOOK_SECRET or settings.EASYPAISA_HASH_KEY
        return settings.PAYMENT_WEBHOOK_SECRET

    @staticmethod
    def _build_reference(prefix: str, order_id: str) -> str:
        clean_order = "".join(ch for ch in order_id if ch.isalnum())[:24] or "ORDER"
        return f"{prefix}-{clean_order}-{int(time.time())}-{uuid.uuid4().hex[:8]}"
