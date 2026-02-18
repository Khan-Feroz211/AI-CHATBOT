from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.api.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)
from src.services.payments import PaymentService

app = FastAPI(
    title="AI Chatbot ML",
    description="ML-powered chatbot API",
    version="3.0.0",
)

payment_service = PaymentService()

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
            "/docs",
        ],
    }


@app.post("/api/v1/payments/create", response_model=PaymentCreateResponse)
async def create_payment(payload: PaymentCreateRequest) -> PaymentCreateResponse:
    return payment_service.create_payment(payload)


@app.post("/api/v1/payments/webhook", response_model=PaymentWebhookResponse)
async def payment_webhook(payload: PaymentWebhookRequest) -> PaymentWebhookResponse:
    return payment_service.handle_webhook(payload)
