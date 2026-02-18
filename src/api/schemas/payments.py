from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PaymentProvider(str, Enum):
    jazzcash = "jazzcash"
    easypaisa = "easypaisa"
    bank_transfer = "bank_transfer"
    cod = "cod"


class PaymentCreateRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    amount_pkr: float = Field(gt=0)
    payment_provider: PaymentProvider
    customer_name: Optional[str] = Field(default=None, max_length=100)
    customer_phone: Optional[str] = Field(default=None, max_length=30)
    note: Optional[str] = Field(default=None, max_length=500)


class PaymentCreateResponse(BaseModel):
    success: bool
    provider: PaymentProvider
    status: str
    reference_id: str
    checkout_url: Optional[str] = None
    instructions: str
    message: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class PaymentWebhookRequest(BaseModel):
    provider: PaymentProvider
    reference_id: str = Field(min_length=1, max_length=128)
    transaction_id: Optional[str] = Field(default=None, max_length=128)
    status: str = Field(min_length=2, max_length=30)
    amount_pkr: Optional[float] = Field(default=None, gt=0)
    signature: Optional[str] = Field(default=None, max_length=512)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class PaymentWebhookResponse(BaseModel):
    accepted: bool
    verified: bool
    message: str
