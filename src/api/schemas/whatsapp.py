from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WhatsAppSendRequest(BaseModel):
    to_phone: str = Field(min_length=8, max_length=30)
    message: str = Field(min_length=1, max_length=4096)
    customer_name: Optional[str] = Field(default=None, max_length=100)
    order_id: Optional[str] = Field(default=None, max_length=64)


class WhatsAppSendResponse(BaseModel):
    success: bool
    status: str
    provider: str = "meta_whatsapp"
    message_id: Optional[str] = None
    to_phone: str
    instructions: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class WhatsAppWebhookEvent(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)


class WhatsAppWebhookAck(BaseModel):
    accepted: bool
    verified: bool
    message: str
