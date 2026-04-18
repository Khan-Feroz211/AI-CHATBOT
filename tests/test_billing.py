"""BazaarBot Day 7 — SaaS billing test suite.

All external HTTP calls (JazzCash, Easypaisa gateways) and PostgreSQL
connections are fully mocked.  No real payments are initiated and no
live database is required.

Coverage:
  - Plan config   (plan tiers, channel rules, LLM flags)
  - JazzCash hash / signature primitives
  - Billing API endpoints via FastAPI TestClient
  - Middleware enforcement (message limit, channel access, LLM gate)

Run:
    pytest tests/test_billing.py -v
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# ── Env bootstrap — must precede ALL bazaarbot imports ────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Core settings
os.environ.setdefault("DATABASE_PATH",   ":memory:")
os.environ.setdefault("SECRET_KEY",      "test-secret")
os.environ.setdefault("ADMIN_PASSWORD",  "testpass")
os.environ.setdefault("JWT_SECRET",      "test-jwt-secret")

# Disable optional heavy dependencies
os.environ.setdefault("USE_LLM_FALLBACK",   "false")
os.environ.setdefault("USE_LANGCHAIN_RAG",  "false")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

# Payment gateway test credentials (sandbox)
os.environ.setdefault("JAZZCASH_INTEGRITY_SALT", "test-integrity-salt")
os.environ.setdefault("JAZZCASH_MERCHANT_ID",    "TEST_MERCHANT")
os.environ.setdefault("JAZZCASH_PASSWORD",       "TEST_PASS")
os.environ.setdefault("EASYPAISA_STORE_ID",      "TEST_STORE")
os.environ.setdefault("EASYPAISA_HASH_KEY",      "test-hash-key")
os.environ.setdefault("EASYPAISA_NTN",           "TEST_NTN")
os.environ.setdefault("FRONTEND_URL",            "http://localhost:5173")
os.environ.setdefault("APP_ENV",                 "sandbox")

# ── Stub asyncpg + database_pg before anything that might trigger them ─────
# Prevents "No module named 'asyncpg'" errors in CI where Postgres is absent.
if "asyncpg" not in sys.modules:
    sys.modules["asyncpg"] = MagicMock()  # type: ignore[assignment]

if "bazaarbot.database_pg" not in sys.modules:
    _stub_db_pg = MagicMock()
    _stub_db_pg.AsyncSessionLocal = MagicMock()
    sys.modules["bazaarbot.database_pg"] = _stub_db_pg  # type: ignore[assignment]

# ── Now safe to import billing code ───────────────────────────────────────
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from bazaarbot.auth.auth_service import create_access_token
from bazaarbot.billing.middleware import get_db
from bazaarbot.billing.payment_service import jazzcash_hash, verify_jazzcash_callback
from bazaarbot.billing.plan_config import (
    PLANS,
    check_channel_allowed,
    check_llm_allowed,
    get_plan,
)
from bazaarbot.config import Config
from bazaarbot.db.billing_models import BillingEvent, Subscription


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════

def _make_token(tenant_slug: str = "test-tenant", role: str = "admin") -> str:
    """Return a signed JWT for the given tenant / role."""
    return create_access_token(tenant_slug, user_id=1, role=role)


def _auth_headers(tenant_slug: str = "test-tenant") -> dict:
    return {"Authorization": f"Bearer {_make_token(tenant_slug)}"}


def _make_subscription(
    *,
    plan: str = "business",
    status: str = "active",
    message_count: int = 0,
    message_limit: int = 5000,
    tenant_slug: str = "test-tenant",
) -> Subscription:
    """Construct an in-memory Subscription instance for testing."""
    plan_cfg = get_plan(plan)
    sub = Subscription()
    sub.id = 1
    sub.sub_id = "test-sub-uuid-0000"
    sub.tenant_slug = tenant_slug
    sub.plan = plan
    sub.status = status
    sub.message_count = message_count
    sub.message_limit = message_limit
    sub.channels_allowed = json.dumps(plan_cfg.channels_allowed)
    sub.llm_enabled = plan_cfg.llm_enabled
    sub.price_pkr = plan_cfg.price_pkr
    sub.billing_cycle = "monthly"
    sub.period_start = datetime.now(timezone.utc) - timedelta(days=1)
    sub.period_end = datetime.now(timezone.utc) + timedelta(days=29)
    sub.gateway = "jazzcash"
    sub.gateway_ref = "TXN-TEST-001"
    sub.cancelled_at = None
    sub.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    return sub


def _build_jazzcash_callback(
    response_code: str = "000",
    plan_id: str = "business",
    tenant_slug: str = "test-tenant",
    salt: str = "test-integrity-salt",
) -> dict:
    """Return a fully signed JazzCash-style callback payload."""
    params: dict = {
        "pp_ResponseCode":  response_code,
        "pp_TxnRefNo":      "TXNTEST001",
        "pp_BillReference": f"billRef-{tenant_slug}",
        "pp_Description":   f"BazaarBot {plan_id} Plan",
        "pp_Amount":        "299900",
    }
    with patch.object(Config, "JAZZCASH_INTEGRITY_SALT", salt):
        params["pp_SecuredHash"] = jazzcash_hash(dict(params))
    return params


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def mock_session() -> AsyncMock:
    """Return a fresh mocked async SQLAlchemy session."""
    session = AsyncMock(spec=AsyncSession)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []

    session.execute = AsyncMock(return_value=mock_result)
    session.scalar = AsyncMock(return_value=0)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture()
def billing_app(mock_session: AsyncMock) -> FastAPI:
    """Minimal FastAPI app with billing router + mocked DB dependency."""
    from bazaarbot.web.billing_routes import router as billing_router

    _app = FastAPI()
    _app.include_router(billing_router)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    _app.dependency_overrides[get_db] = _override_get_db
    return _app


@pytest.fixture()
def client(billing_app: FastAPI) -> TestClient:
    return TestClient(billing_app, raise_server_exceptions=True)


# ══════════════════════════════════════════════════════════════════════════
# 1. Plan config — unit tests (no HTTP / DB)
# ══════════════════════════════════════════════════════════════════════════

def test_all_plans_defined():
    """All three SaaS tiers must be present with correct PKR pricing."""
    assert "starter"  in PLANS
    assert "business" in PLANS
    assert "pro"      in PLANS

    assert PLANS["starter"].price_pkr  == 999
    assert PLANS["business"].price_pkr == 2999
    assert PLANS["pro"].price_pkr      == 7999


def test_channel_allowed_starter():
    """Starter plan allows WhatsApp but not Telegram or web."""
    assert check_channel_allowed("starter", "whatsapp") is True
    assert check_channel_allowed("starter", "telegram") is False
    assert check_channel_allowed("starter", "web")      is False


def test_channel_allowed_business():
    """Business plan includes WhatsApp and Telegram."""
    assert check_channel_allowed("business", "whatsapp") is True
    assert check_channel_allowed("business", "telegram") is True


def test_channel_allowed_pro():
    """Pro plan allows all four channels."""
    for ch in ("whatsapp", "telegram", "web", "api"):
        assert check_channel_allowed("pro", ch) is True, f"pro should allow {ch}"


def test_llm_disabled_on_starter():
    """Starter plan must NOT enable LLM replies."""
    assert check_llm_allowed("starter") is False


def test_llm_enabled_on_business():
    """Business plan must enable LLM replies."""
    assert check_llm_allowed("business") is True


def test_llm_enabled_on_pro():
    """Pro plan must enable LLM replies."""
    assert check_llm_allowed("pro") is True


def test_plan_message_limits():
    """Message limits must match the documented tier limits."""
    assert PLANS["starter"].message_limit  == 500
    assert PLANS["business"].message_limit == 5000
    # Pro is effectively unlimited (a very large number)
    assert PLANS["pro"].message_limit >= 100_000


# ══════════════════════════════════════════════════════════════════════════
# 2. Payment service — hash / signature tests
# ══════════════════════════════════════════════════════════════════════════

def test_jazzcash_hash_consistent():
    """jazzcash_hash() must be deterministic — same input → same output."""
    params = {"pp_Amount": "99900", "pp_TxnRefNo": "TXN123TEST"}
    with patch.object(Config, "JAZZCASH_INTEGRITY_SALT", "test-integrity-salt"):
        hash1 = jazzcash_hash(params.copy())
        hash2 = jazzcash_hash(params.copy())
    assert hash1 == hash2, "JazzCash hash must be deterministic"
    assert len(hash1) == 64, "HMAC-SHA256 hex digest must be 64 chars"


def test_jazzcash_hash_changes_with_params():
    """Different params must produce different hashes."""
    with patch.object(Config, "JAZZCASH_INTEGRITY_SALT", "test-integrity-salt"):
        h1 = jazzcash_hash({"pp_Amount": "100"})
        h2 = jazzcash_hash({"pp_Amount": "200"})
    assert h1 != h2


def test_verify_jazzcash_callback_valid():
    """verify_jazzcash_callback() must return True for a correctly signed payload."""
    params = {"pp_Amount": "99900", "pp_TxnRefNo": "TXN_VALID"}
    with patch.object(Config, "JAZZCASH_INTEGRITY_SALT", "test-integrity-salt"):
        sig = jazzcash_hash(dict(params))
        params["pp_SecuredHash"] = sig
        assert verify_jazzcash_callback(params) is True


def test_verify_jazzcash_callback_invalid():
    """verify_jazzcash_callback() must return False for a tampered hash."""
    params = {
        "pp_Amount":      "99900",
        "pp_TxnRefNo":    "TXN_TAMPERED",
        "pp_SecuredHash": "0" * 64,
    }
    with patch.object(Config, "JAZZCASH_INTEGRITY_SALT", "test-integrity-salt"):
        assert verify_jazzcash_callback(params) is False


# ══════════════════════════════════════════════════════════════════════════
# 3. GET /api/billing/plans
# ══════════════════════════════════════════════════════════════════════════

def test_plans_endpoint_public(client: TestClient):
    """GET /api/billing/plans must return 200 and exactly 3 plan objects."""
    resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert {p["plan_id"] for p in data} == {"starter", "business", "pro"}


def test_plans_endpoint_required_fields(client: TestClient):
    """Each plan object must contain all documented response fields."""
    resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    for plan in resp.json():
        for field in (
            "plan_id", "name", "price_pkr", "price_display",
            "message_limit", "channels", "llm_enabled",
            "features", "is_current", "is_popular",
        ):
            assert field in plan, f"'{field}' missing from plan {plan.get('plan_id')}"


def test_plans_price_display_format(client: TestClient):
    """price_display must be formatted as 'PKR {price}/month'."""
    resp = client.get("/api/billing/plans")
    data = resp.json()
    starter  = next(p for p in data if p["plan_id"] == "starter")
    business = next(p for p in data if p["plan_id"] == "business")
    assert starter["price_display"]  == "PKR 999/month"
    assert business["price_display"] == "PKR 2,999/month"


def test_plans_business_is_popular(client: TestClient):
    """Business plan must have is_popular=True; others must have False."""
    resp = client.get("/api/billing/plans")
    for plan in resp.json():
        if plan["plan_id"] == "business":
            assert plan["is_popular"] is True
        else:
            assert plan["is_popular"] is False, (
                f"plan '{plan['plan_id']}' should not be marked popular"
            )


def test_plans_is_current_marked_with_jwt(
    client: TestClient, mock_session: AsyncMock
):
    """When a valid JWT is provided and tenant has a subscription,
    the matching plan must have is_current=True."""
    sub = _make_subscription(plan="business")
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.get("/api/billing/plans", headers=_auth_headers())
    data = resp.json()
    business = next(p for p in data if p["plan_id"] == "business")
    assert business["is_current"] is True
    for plan in (p for p in data if p["plan_id"] != "business"):
        assert plan["is_current"] is False


# ══════════════════════════════════════════════════════════════════════════
# 4. GET /api/billing/usage
# ══════════════════════════════════════════════════════════════════════════

def test_usage_endpoint_requires_auth(client: TestClient):
    """GET /api/billing/usage without a token must be rejected (401/403)."""
    resp = client.get("/api/billing/usage")
    assert resp.status_code in (401, 403)


def test_usage_returns_free_trial_info(
    client: TestClient, mock_session: AsyncMock
):
    """With no subscription row, endpoint must report free_trial."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.scalar  = AsyncMock(return_value=42)  # 42 inbound msgs

    resp = client.get("/api/billing/usage", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"] == "free_trial"
    assert data["message_limit"] == 200  # FREE_TRIAL_MESSAGES constant
    assert data["messages_used"] == 42


def test_usage_returns_paid_plan_info(
    client: TestClient, mock_session: AsyncMock
):
    """With an active business subscription, endpoint must return accurate fields."""
    sub = _make_subscription(plan="business", message_count=1234)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.get("/api/billing/usage", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"]          == "business"
    assert data["messages_used"] == 1234
    assert data["message_limit"] == 5000
    assert data["llm_enabled"]   is True
    assert data["price_pkr"]     == 2999


def test_usage_percent_calculated(client: TestClient, mock_session: AsyncMock):
    """percent_used must be (messages_used / message_limit) * 100."""
    sub = _make_subscription(plan="starter", message_count=250, message_limit=500)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.get("/api/billing/usage", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert abs(data["percent_used"] - 50.0) < 0.1


# ══════════════════════════════════════════════════════════════════════════
# 5. POST /api/billing/checkout
# ══════════════════════════════════════════════════════════════════════════

_MOCK_JAZZCASH_RESULT = {
    "gateway":      "jazzcash",
    "txn_ref":      "TXNTEST123",
    "redirect_url": "https://sandbox.jazzcash.com.pk/ApplicationRequestServlet",
    "params":       {"pp_Amount": "299900"},
    "amount_pkr":   2999,
    "expires_at":   "20260101000000",
}

_MOCK_EASYPAISA_RESULT = {
    "gateway":      "easypaisa",
    "order_id":     "EPTEST456",
    "redirect_url": "https://easypaisa.com.pk/easypay/Index",
    "amount_pkr":   2999,
    "store_id":     "TEST_STORE",
    "params":       {"storeId": "TEST_STORE"},
}


def test_checkout_jazzcash(client: TestClient, mock_session: AsyncMock):
    """Valid JazzCash checkout must return redirect_url and txn_ref."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    with patch(
        "bazaarbot.web.billing_routes.create_jazzcash_checkout",
        new_callable=AsyncMock,
        return_value=_MOCK_JAZZCASH_RESULT,
    ):
        resp = client.post(
            "/api/billing/checkout",
            json={
                "plan":         "business",
                "gateway":      "jazzcash",
                "phone_number": "+923001234567",
            },
            headers=_auth_headers(),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "redirect_url" in data
    assert "txn_ref"      in data
    assert data["gateway"] == "jazzcash"


def test_checkout_easypaisa(client: TestClient, mock_session: AsyncMock):
    """Valid Easypaisa checkout must return redirect_url and order_id."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    with patch(
        "bazaarbot.web.billing_routes.create_easypaisa_checkout",
        new_callable=AsyncMock,
        return_value=_MOCK_EASYPAISA_RESULT,
    ):
        resp = client.post(
            "/api/billing/checkout",
            json={
                "plan":         "starter",
                "gateway":      "easypaisa",
                "phone_number": "+923451234567",
            },
            headers=_auth_headers(),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "redirect_url" in data
    assert data["gateway"] == "easypaisa"


def test_checkout_same_plan_rejected(client: TestClient, mock_session: AsyncMock):
    """Purchasing the tenant's current plan must return HTTP 400."""
    sub = _make_subscription(plan="business")
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.post(
        "/api/billing/checkout",
        json={
            "plan":         "business",
            "gateway":      "jazzcash",
            "phone_number": "+923001234567",
        },
        headers=_auth_headers(),
    )
    assert resp.status_code == 400


def test_checkout_invalid_plan(client: TestClient):
    """An unknown plan name must return HTTP 400."""
    resp = client.post(
        "/api/billing/checkout",
        json={"plan": "diamond", "gateway": "jazzcash", "phone_number": "+923001234567"},
        headers=_auth_headers(),
    )
    assert resp.status_code == 400


def test_checkout_invalid_phone(client: TestClient, mock_session: AsyncMock):
    """Phone without +92 prefix must return HTTP 400."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.post(
        "/api/billing/checkout",
        json={"plan": "starter", "gateway": "jazzcash", "phone_number": "03001234567"},
        headers=_auth_headers(),
    )
    assert resp.status_code == 400


def test_checkout_invalid_gateway(client: TestClient, mock_session: AsyncMock):
    """Unknown gateway name must return HTTP 400."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.post(
        "/api/billing/checkout",
        json={"plan": "starter", "gateway": "stripe", "phone_number": "+923001234567"},
        headers=_auth_headers(),
    )
    assert resp.status_code == 400


def test_checkout_requires_auth(client: TestClient):
    """POST /api/billing/checkout without a token must be rejected."""
    resp = client.post(
        "/api/billing/checkout",
        json={"plan": "starter", "gateway": "jazzcash", "phone_number": "+923001234567"},
    )
    assert resp.status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════
# 6. JazzCash callback
# ══════════════════════════════════════════════════════════════════════════

def test_jazzcash_callback_success(client: TestClient, mock_session: AsyncMock):
    """Callback with valid sig + code 000 must activate subscription and redirect."""
    sub = _make_subscription()

    with (
        patch(
            "bazaarbot.web.billing_routes.verify_jazzcash_callback",
            return_value=True,
        ),
        patch(
            "bazaarbot.web.billing_routes.activate_subscription",
            new_callable=AsyncMock,
            return_value=sub,
        ) as mock_activate,
    ):
        params = _build_jazzcash_callback(response_code="000")
        resp = client.post(
            "/api/billing/jazzcash/callback",
            data=params,
            follow_redirects=False,
        )

    assert resp.status_code in (302, 307)
    assert "/billing/success" in resp.headers.get("location", "")
    mock_activate.assert_called_once()


def test_jazzcash_callback_invalid_sig(client: TestClient):
    """Tampered signature must return HTTP 400."""
    params = {
        "pp_ResponseCode":  "000",
        "pp_TxnRefNo":      "TXN_BAD_SIG",
        "pp_BillReference": "billRef-test-tenant",
        "pp_Description":   "BazaarBot business Plan",
        "pp_Amount":        "299900",
        "pp_SecuredHash":   "0" * 64,
    }
    resp = client.post(
        "/api/billing/jazzcash/callback",
        data=params,
    )
    assert resp.status_code == 400


def test_jazzcash_callback_failed_payment(client: TestClient, mock_session: AsyncMock):
    """Callback with non-000 code must redirect to /billing/failed."""
    with patch(
        "bazaarbot.web.billing_routes.verify_jazzcash_callback",
        return_value=True,
    ):
        params = _build_jazzcash_callback(response_code="111")
        resp = client.post(
            "/api/billing/jazzcash/callback",
            data=params,
            follow_redirects=False,
        )

    assert resp.status_code in (302, 307)
    assert "/billing/failed" in resp.headers.get("location", "")


def test_jazzcash_callback_internal_error_returns_200(client: TestClient):
    """An unexpected exception inside the callback must still return HTTP 200."""
    with patch(
        "bazaarbot.web.billing_routes.verify_jazzcash_callback",
        side_effect=Exception("simulated internal error"),
    ):
        resp = client.post(
            "/api/billing/jazzcash/callback",
            data={"pp_ResponseCode": "000"},
        )
    assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# 7. Subscription cancel + billing history
# ══════════════════════════════════════════════════════════════════════════

def test_cancel_subscription(client: TestClient, mock_session: AsyncMock):
    """POST /cancel must set status to 'cancelled' and cancelled_at."""
    sub = _make_subscription(plan="business", status="active")
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.post("/api/billing/cancel", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    # Verify the ORM object was mutated in-place
    assert sub.status == "cancelled"
    assert sub.cancelled_at is not None


def test_cancel_no_subscription_returns_404(
    client: TestClient, mock_session: AsyncMock
):
    """POST /cancel when there is no active subscription must return 404."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.post("/api/billing/cancel", headers=_auth_headers())
    assert resp.status_code == 404


def test_cancel_requires_auth(client: TestClient):
    """POST /api/billing/cancel without a token must be rejected."""
    resp = client.post("/api/billing/cancel")
    assert resp.status_code in (401, 403)


def test_billing_history_requires_auth(client: TestClient):
    """GET /api/billing/history without a token must be rejected."""
    resp = client.get("/api/billing/history")
    assert resp.status_code in (401, 403)


def test_billing_history_returns_list(client: TestClient, mock_session: AsyncMock):
    """GET /api/billing/history must return a JSON list of events."""
    event = BillingEvent()
    event.id = 1
    event.event_id = "evt-uuid-001"
    event.tenant_slug = "test-tenant"
    event.event_type = "payment_succeeded"
    event.plan = "business"
    event.amount_pkr = 2999
    event.gateway = "jazzcash"
    event.gateway_data = "{}"
    event.created_at = datetime.now(timezone.utc)

    result = MagicMock()
    result.scalars.return_value.all.return_value = [event]
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.get("/api/billing/history", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["event_type"] == "payment_succeeded"


def test_billing_history_empty_list(client: TestClient, mock_session: AsyncMock):
    """GET /api/billing/history must return [] when no events exist."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)

    resp = client.get("/api/billing/history", headers=_auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


# ══════════════════════════════════════════════════════════════════════════
# 8. Middleware — enforce_message_limit, check_llm_access, increment
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_message_limit_enforcement():
    """enforce_message_limit must raise HTTP 429 when quota is exhausted."""
    # Tenant on Starter plan with counter at the limit
    sub = _make_subscription(plan="starter", message_count=500, message_limit=500)

    mock_db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_db.execute = AsyncMock(return_value=result)
    mock_db.scalar = AsyncMock(return_value=500)

    from bazaarbot.billing.middleware import enforce_message_limit

    with pytest.raises(HTTPException) as exc_info:
        await enforce_message_limit("test-tenant", "whatsapp", mock_db)

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_message_limit_allowed_when_under_quota():
    """enforce_message_limit must NOT raise when usage is below the limit."""
    sub = _make_subscription(plan="business", message_count=100, message_limit=5000)

    mock_db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_db.execute = AsyncMock(return_value=result)
    mock_db.scalar = AsyncMock(return_value=100)

    from bazaarbot.billing.middleware import enforce_message_limit

    # Should not raise
    await enforce_message_limit("test-tenant", "whatsapp", mock_db)


@pytest.mark.asyncio
async def test_channel_not_allowed_enforcement():
    """enforce_message_limit must raise HTTP 403 for a disallowed channel."""
    # Starter plan only allows WhatsApp — Telegram is blocked
    sub = _make_subscription(plan="starter", message_count=0, message_limit=500)
    sub.channels_allowed = '["whatsapp"]'

    mock_db = AsyncMock(spec=AsyncSession)
    # Two execute() calls: check_message_limit + get_tenant_subscription
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_db.execute = AsyncMock(return_value=result)
    mock_db.scalar = AsyncMock(return_value=0)

    from bazaarbot.billing.middleware import enforce_message_limit

    with pytest.raises(HTTPException) as exc_info:
        await enforce_message_limit("test-tenant", "telegram", mock_db)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_check_llm_access_false_for_starter():
    """check_llm_access must return False for a Starter subscriber."""
    sub = _make_subscription(plan="starter")

    mock_db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_db.execute = AsyncMock(return_value=result)

    from bazaarbot.billing.middleware import check_llm_access

    allowed = await check_llm_access("test-tenant", mock_db)
    assert allowed is False


@pytest.mark.asyncio
async def test_check_llm_access_true_for_business():
    """check_llm_access must return True for a Business subscriber."""
    sub = _make_subscription(plan="business")

    mock_db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = sub
    mock_db.execute = AsyncMock(return_value=result)

    from bazaarbot.billing.middleware import check_llm_access

    allowed = await check_llm_access("test-tenant", mock_db)
    assert allowed is True


@pytest.mark.asyncio
async def test_check_llm_access_false_for_free_trial():
    """check_llm_access must return False when tenant has no subscription."""
    mock_db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # free trial
    mock_db.execute = AsyncMock(return_value=result)

    from bazaarbot.billing.middleware import check_llm_access

    allowed = await check_llm_access("unsubscribed-tenant", mock_db)
    assert allowed is False


@pytest.mark.asyncio
async def test_increment_message_count_executes_update():
    """increment_message_count must call db.execute() exactly once."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock()

    from bazaarbot.billing.middleware import increment_message_count

    await increment_message_count("test-tenant", mock_db)
    mock_db.execute.assert_called_once()
