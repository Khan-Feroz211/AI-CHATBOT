from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from config.settings import settings
from src.api.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)
from src.api.schemas.whatsapp import (
    WhatsAppSendRequest,
    WhatsAppSendResponse,
    WhatsAppWebhookAck,
    WhatsAppWebhookEvent,
)
from src.services.payments import PaymentService
from src.services.whatsapp import WhatsAppService

app = FastAPI(
    title="AI Chatbot ML",
    description="ML-powered chatbot API",
    version="3.0.0",
)

payment_service = PaymentService()
whatsapp_service = WhatsAppService()

cors_origins = list(settings.CORS_ORIGINS)
for extra_origin in ("http://localhost:8080", "http://127.0.0.1:8080"):
    if extra_origin not in cors_origins:
        cors_origins.append(extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Chatbot ML!",
        "version": "3.0.0",
        "architecture": "ML Workflow",
        "status": "ready",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api"}


@app.get("/api/v1/info")
async def info():
    return {
        "features": [
            "Task Management",
            "Note Taking",
            "ML Predictions",
            "User Authentication",
            "Payments (JazzCash/EasyPaisa/Bank/COD)",
        ],
        "endpoints": [
            "/",
            "/health",
            "/api/v1/info",
            "/api/v1/payments/create",
            "/api/v1/payments/webhook",
            "/api/v1/whatsapp/send",
            "/api/v1/whatsapp/webhook",
            "/docs",
        ],
    }


@app.post("/api/v1/payments/create", response_model=PaymentCreateResponse)
async def create_payment(payload: PaymentCreateRequest) -> PaymentCreateResponse:
    return payment_service.create_payment(payload)


@app.post("/api/v1/payments/webhook", response_model=PaymentWebhookResponse)
async def payment_webhook(payload: PaymentWebhookRequest) -> PaymentWebhookResponse:
    return payment_service.handle_webhook(payload)


@app.post("/api/v1/whatsapp/send", response_model=WhatsAppSendResponse)
async def whatsapp_send(payload: WhatsAppSendRequest) -> WhatsAppSendResponse:
    return whatsapp_service.build_outbound_message(payload)


@app.get("/api/v1/whatsapp/webhook", response_class=PlainTextResponse)
async def whatsapp_webhook_verify(
    hub_mode: Optional[str] = Query(default=None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
):
    challenge = whatsapp_service.verify_webhook_challenge(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        raise HTTPException(status_code=403, detail="Webhook verification failed")
    return challenge


@app.post("/api/v1/whatsapp/webhook", response_model=WhatsAppWebhookAck)
async def whatsapp_webhook_event(
    payload: WhatsAppWebhookEvent,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(default=None),
) -> WhatsAppWebhookAck:
    raw_body = await request.body()
    verified = whatsapp_service.verify_webhook_signature(raw_body, x_hub_signature_256)
    if not verified:
        return WhatsAppWebhookAck(
            accepted=False,
            verified=False,
            message="Invalid webhook signature",
        )
    return WhatsAppWebhookAck(
        accepted=True,
        verified=True,
        message=f"Webhook accepted (keys={list(payload.payload.keys())[:6]})",
    )
