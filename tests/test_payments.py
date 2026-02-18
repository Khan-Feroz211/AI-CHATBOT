from src.api.schemas.payments import PaymentCreateRequest, PaymentProvider, PaymentWebhookRequest
from src.services.payments import PaymentService


def test_create_jazzcash_payment_in_sandbox():
    service = PaymentService()
    payload = PaymentCreateRequest(
        order_id="ORD-1001",
        amount_pkr=3500,
        payment_provider=PaymentProvider.jazzcash,
    )
    result = service.create_payment(payload)
    assert result.success is True
    assert result.provider == PaymentProvider.jazzcash
    assert result.reference_id.startswith("JC-")


def test_create_bank_transfer_instructions():
    service = PaymentService()
    payload = PaymentCreateRequest(
        order_id="ORD-2002",
        amount_pkr=1500,
        payment_provider=PaymentProvider.bank_transfer,
    )
    result = service.create_payment(payload)
    assert result.success is True
    assert "Transfer PKR" in result.instructions


def test_webhook_accepts_in_sandbox():
    service = PaymentService()
    webhook = PaymentWebhookRequest(
        provider=PaymentProvider.easypaisa,
        reference_id="EP-ORD-1-123456",
        status="paid",
        amount_pkr=2200,
        signature="any",
    )
    result = service.handle_webhook(webhook)
    assert result.accepted is True
    assert result.verified is True
